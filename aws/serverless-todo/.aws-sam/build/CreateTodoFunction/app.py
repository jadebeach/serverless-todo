import json
import uuid
import os
import boto3
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
    """Todo作成のLambdaハンドラ"""
    
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # リクエストボディをパース
        body = json.loads(event['body'])
        print(f"Parsed body: {body}")
        
        # バリデーション: 必須フィールド
        required_fields = ['title', 'dueDate', 'priority']
        for field in required_fields:
            if field not in body or not body[field]:
                return create_response(400, {
                    'error': f'Missing required field: {field}'
                })
        
        # priorityの値チェック
        valid_priorities = ['HIGH', 'MEDIUM', 'LOW']
        if body['priority'] not in valid_priorities:
            return create_response(400, {
                'error': f'Invalid priority. Must be one of: {valid_priorities}'
            })
        
        # ユーザーID（後でCognitoから取得）
        user_id = 'test-user-001'
        
        # タスクデータ作成
        task_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        # DynamoDBアイテム
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
        
        # DynamoDBに保存
        table.put_item(Item=item)
        
        print("Successfully saved to DynamoDB")
        
        # 成功レスポンス
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