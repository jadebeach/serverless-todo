import os
import sys
import json
import uuid
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import boto3
from common.auth_helper import get_user_id_from_event
from datetime import datetime

# DynamoDBクライアント初期化
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def create_response(status_code, body):
    """API Gatewayレスポンスを生成"""
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

def lambda_handler(event, context):

    print(f"Received event: {json.dumps(event)}")
    
    try:
        body = json.loads(event['body'])
        print(f"Parsed body: {body}")
        
        required_fields = ['title', 'dueDate', 'priority']
        for field in required_fields:
            if field not in body or not body[field]:
                return create_response(400, {
                    'error': f'Missing required field: {field}'
                })
        
        valid_priorities = ['HIGH', 'MEDIUM', 'LOW']
        if body['priority'] not in valid_priorities:
            return create_response(400, {
                'error': f'Invalid priority. Must be one of: {valid_priorities}'
            })
        
        user_id = get_user_id_from_event(event)
        
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
        print(f"Saving item: {json.dumps(item, default=str)}")
        
        table.put_item(Item=item)
        
        print("Successfully saved to DynamoDB")
        
        return create_response(201, {
            'message': 'Todo created successfully',
            'todo': item
        })
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return create_response(400, {'error': 'Invalid JSON format'})
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return create_response(500, {
            'error': 'Internal server error',
            'message': str(e)
        })
