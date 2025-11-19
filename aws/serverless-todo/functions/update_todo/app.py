import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime

# DynamoDBクライアント
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def create_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body, ensure_ascii=False)
    }

def find_task_by_id(user_id, task_id):
    """taskIdからタスクを検索してPK+SKを取得"""
    try:
        response = table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{user_id}')
        )
        
        items = response.get('Items', [])
        
        # taskIdが一致するアイテムを探す
        for item in items:
            if item.get('taskId') == task_id:
                return item
        
        return None
        
    except Exception as e:
        print(f"Error finding task: {e}")
        return None

def lambda_handler(event, context):
    """タスク更新のLambdaハンドラ"""
    
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # パスパラメータからtaskId取得
        path_params = event.get('pathParameters', {})
        task_id = path_params.get('taskId')
        
        if not task_id:
            return create_response(400, {'error': 'taskId is required'})
        
        # リクエストボディをパース
        body = json.loads(event['body'])
        print(f"Update request for taskId={task_id}, body={body}")
        
        # ユーザーID取得（後でCognitoから）
        user_id = get_user_id_from_event(event)
        
        # タスクを検索
        existing_task = find_task_by_id(user_id, task_id)
        
        if not existing_task:
            return create_response(404, {
                'error': 'Task not found',
                'taskId': task_id
            })
        
        # 更新可能なフィールド
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        # title更新
        if 'title' in body:
            update_expression_parts.append('#title = :title')
            expression_attribute_names['#title'] = 'title'
            expression_attribute_values[':title'] = body['title']
        
        # description更新
        if 'description' in body:
            update_expression_parts.append('description = :description')
            expression_attribute_values[':description'] = body['description']
        
        # dueDate更新
        if 'dueDate' in body:
            update_expression_parts.append('dueDate = :dueDate')
            expression_attribute_values[':dueDate'] = body['dueDate']
            
            # GSI1SKも更新（期限変更時）
            priority = body.get('priority', existing_task.get('priority', 'MEDIUM'))
            update_expression_parts.append('GSI1SK = :gsi1sk')
            expression_attribute_values[':gsi1sk'] = f"DUE#{body['dueDate']}#{priority}"
        
        # priority更新
        if 'priority' in body:
            valid_priorities = ['HIGH', 'MEDIUM', 'LOW']
            if body['priority'] not in valid_priorities:
                return create_response(400, {
                    'error': f'Invalid priority. Must be one of: {valid_priorities}'
                })
            
            update_expression_parts.append('priority = :priority')
            expression_attribute_values[':priority'] = body['priority']
            
            # GSI1SKも更新（優先度変更時）
            due_date = body.get('dueDate', existing_task.get('dueDate'))
            update_expression_parts.append('GSI1SK = :gsi1sk')
            expression_attribute_values[':gsi1sk'] = f"DUE#{due_date}#{body['priority']}"
        
        # status更新
        if 'status' in body:
            valid_statuses = ['PENDING', 'COMPLETED']
            if body['status'] not in valid_statuses:
                return create_response(400, {
                    'error': f'Invalid status. Must be one of: {valid_statuses}'
                })
            
            update_expression_parts.append('#status = :status')
            expression_attribute_names['#status'] = 'status'
            expression_attribute_values[':status'] = body['status']
        
        # 更新項目がない場合
        if not update_expression_parts:
            return create_response(400, {'error': 'No fields to update'})
        
        # updatedAt更新（必須）
        current_time = datetime.utcnow().isoformat() + 'Z'
        update_expression_parts.append('updatedAt = :updatedAt')
        expression_attribute_values[':updatedAt'] = current_time
        
        # UpdateExpression構築
        update_expression = 'SET ' + ', '.join(update_expression_parts)
        
        print(f"UpdateExpression: {update_expression}")
        print(f"ExpressionAttributeValues: {expression_attribute_values}")
        
        # DynamoDB更新
        update_params = {
            'Key': {
                'PK': existing_task['PK'],
                'SK': existing_task['SK']
            },
            'UpdateExpression': update_expression,
            'ExpressionAttributeValues': expression_attribute_values,
            'ReturnValues': 'ALL_NEW'
        }
        
        if expression_attribute_names:
            update_params['ExpressionAttributeNames'] = expression_attribute_names
        
        response = table.update_item(**update_params)
        
        updated_item = response['Attributes']
        
        # レスポンス用に整形
        clean_item = {
            'taskId': updated_item['taskId'],
            'title': updated_item['title'],
            'description': updated_item.get('description', ''),
            'dueDate': updated_item['dueDate'],
            'priority': updated_item['priority'],
            'status': updated_item['status'],
            'createdAt': updated_item['createdAt'],
            'updatedAt': updated_item['updatedAt']
        }
        
        return create_response(200, {
            'message': 'Task updated successfully',
            'task': clean_item
        })
        
    except json.JSONDecodeError:
        return create_response(400, {'error': 'Invalid JSON format'})
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return create_response(500, {
            'error': 'Internal server error',
            'message': str(e)
        })

