import json
import uuid
import os
import boto3
from datetime import datetime

# DynamoDBクライアント
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    """タスク作成"""
    
    print(f"Event: {json.dumps(event)}")
    
    try:
        # リクエストボディ解析
        body = json.loads(event['body'])
        print(f"Body: {body}")
        
        # 必須フィールドチェック
        if 'title' not in body or not body['title']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'title is required'})
            }
        
        if 'dueDate' not in body or not body['dueDate']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'dueDate is required'})
            }
        
        if 'priority' not in body or not body['priority']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'priority is required'})
            }
        
        # priorityチェック
        if body['priority'] not in ['HIGH', 'MEDIUM', 'LOW']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'priority must be HIGH, MEDIUM, or LOW'})
            }
        
        # データ作成
        user_id = 'test-user-001'
        task_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        item = {
            'PK': f'USER#{user_id}',
            'SK': f'TODO#{current_time}#{task_id}',
            'GSI1PK': f'USER#{user_id}',
            'GSI1SK': f'DUE#{body["dueDate"]}#{body["priority"]}',
            'taskId': task_id,
            'title': body['title'],
            'description': body.get('description', ''),
            'dueDate': body['dueDate'],
            'priority': body['priority'],
            'status': 'PENDING',
            'createdAt': current_time,
            'updatedAt': current_time
        }
        
        print(f"Saving: {json.dumps(item, default=str)}")
        
        # DynamoDB保存
        table.put_item(Item=item)
        
        print("Success!")
        
        # レスポンス
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Task created successfully',
                'todo': {
                    'taskId': item['taskId'],
                    'title': item['title'],
                    'description': item['description'],
                    'dueDate': item['dueDate'],
                    'priority': item['priority'],
                    'status': item['status'],
                    'createdAt': item['createdAt'],
                    'updatedAt': item['updatedAt']
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