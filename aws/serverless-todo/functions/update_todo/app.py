import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime

# DynamoDBクライアント
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def find_task(user_id, task_id):
    """taskIdからタスクを検索"""
    try:
        response = table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{user_id}')
        )
        
        for item in response.get('Items', []):
            if item.get('taskId') == task_id:
                return item
        
        return None
    except Exception as e:
        print(f"Error finding task: {e}")
        return None

def lambda_handler(event, context):
    """タスク更新"""
    
    print(f"Event: {json.dumps(event)}")
    
    try:
        # パスパラメータからtaskId取得
        task_id = event.get('pathParameters', {}).get('taskId')
        if not task_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'taskId is required'})
            }
        
        # リクエストボディ解析
        body = json.loads(event['body'])
        print(f"Update taskId={task_id}, body={body}")
        
        # ユーザーID（固定）
        user_id = 'test-user-001'
        
        # タスク検索
        existing_task = find_task(user_id, task_id)
        if not existing_task:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Task not found', 'taskId': task_id})
            }
        
        print(f"Found task: {existing_task['PK']}, {existing_task['SK']}")
        
        # 更新式を構築
        update_parts = []
        attr_values = {}
        attr_names = {}
        
        # title更新
        if 'title' in body:
            update_parts.append('#title = :title')
            attr_names['#title'] = 'title'
            attr_values[':title'] = body['title']
        
        # description更新
        if 'description' in body:
            update_parts.append('description = :description')
            attr_values[':description'] = body['description']
        
        # dueDate更新
        if 'dueDate' in body:
            update_parts.append('dueDate = :dueDate')
            attr_values[':dueDate'] = body['dueDate']
            
            # GSI1SKも更新
            priority = body.get('priority', existing_task.get('priority', 'MEDIUM'))
            update_parts.append('GSI1SK = :gsi1sk')
            attr_values[':gsi1sk'] = f"DUE#{body['dueDate']}#{priority}"
        
        # priority更新
        if 'priority' in body:
            if body['priority'] not in ['HIGH', 'MEDIUM', 'LOW']:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'priority must be HIGH, MEDIUM, or LOW'})
                }
            
            update_parts.append('priority = :priority')
            attr_values[':priority'] = body['priority']
            
            # GSI1SKも更新
            due_date = body.get('dueDate', existing_task.get('dueDate'))
            update_parts.append('GSI1SK = :gsi1sk')
            attr_values[':gsi1sk'] = f"DUE#{due_date}#{body['priority']}"
        
        # status更新
        if 'status' in body:
            if body['status'] not in ['PENDING', 'COMPLETED']:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'status must be PENDING or COMPLETED'})
                }
            
            update_parts.append('#status = :status')
            attr_names['#status'] = 'status'
            attr_values[':status'] = body['status']
        
        # 更新項目なし
        if not update_parts:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'No fields to update'})
            }
        
        # updatedAt追加
        current_time = datetime.utcnow().isoformat() + 'Z'
        update_parts.append('updatedAt = :updatedAt')
        attr_values[':updatedAt'] = current_time
        
        # UpdateExpression構築
        update_expression = 'SET ' + ', '.join(update_parts)
        
        print(f"UpdateExpression: {update_expression}")
        print(f"AttributeValues: {attr_values}")
        
        # DynamoDB更新
        update_params = {
            'Key': {
                'PK': existing_task['PK'],
                'SK': existing_task['SK']
            },
            'UpdateExpression': update_expression,
            'ExpressionAttributeValues': attr_values,
            'ReturnValues': 'ALL_NEW'
        }
        
        if attr_names:
            update_params['ExpressionAttributeNames'] = attr_names
        
        response = table.update_item(**update_params)
        updated_item = response['Attributes']
        
        print("Update successful!")
        
        # レスポンス
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Task updated successfully',
                'task': {
                    'taskId': updated_item['taskId'],
                    'title': updated_item['title'],
                    'description': updated_item.get('description', ''),
                    'dueDate': updated_item['dueDate'],
                    'priority': updated_item['priority'],
                    'status': updated_item['status'],
                    'createdAt': updated_item['createdAt'],
                    'updatedAt': updated_item['updatedAt']
                }
            }, ensure_ascii=False)
        }
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Invalid JSON'})
        }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }