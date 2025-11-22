import json
import os
import boto3
from boto3.dynamodb.conditions import Key

# DynamoDBクライアント
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    """タスク一覧取得"""
    
    print(f"Event: {json.dumps(event)}")
    
    try:
        # クエリパラメータ
        params = event.get('queryStringParameters') or {}
        status_filter = params.get('status')
        limit = int(params.get('limit', 20))
        sort_by = params.get('sortBy', 'dueDate')
        
        print(f"Params - status: {status_filter}, limit: {limit}, sortBy: {sort_by}")
        
        # ユーザーID（固定）
        user_id = 'test-user-001'
        
        # クエリ構築
        if sort_by == 'dueDate':
            # GSI1で期限順
            query_params = {
                'IndexName': 'GSI1',
                'KeyConditionExpression': Key('GSI1PK').eq(f'USER#{user_id}'),
                'Limit': limit,
                'ScanIndexForward': True
            }
        else:
            # メインテーブルで作成日順
            query_params = {
                'KeyConditionExpression': Key('PK').eq(f'USER#{user_id}'),
                'Limit': limit,
                'ScanIndexForward': False
            }
        
        print(f"Query: {query_params}")
        
        # DynamoDBクエリ
        response = table.query(**query_params)
        items = response.get('Items', [])
        
        print(f"Retrieved {len(items)} items")
        
        # ステータスフィルタ
        if status_filter:
            print(f"Filtering by status: {status_filter}")
            items = [item for item in items if item.get('status') == status_filter]
            print(f"After filter: {len(items)} items")
        
        # レスポンス用に整形
        clean_items = []
        for item in items:
            clean_items.append({
                'taskId': item['taskId'],
                'title': item['title'],
                'description': item.get('description', ''),
                'dueDate': item['dueDate'],
                'priority': item['priority'],
                'status': item['status'],
                'createdAt': item['createdAt'],
                'updatedAt': item['updatedAt']
            })
        
        result = {
            'items': clean_items,
            'count': len(clean_items)
        }
        
        print(f"Returning {len(clean_items)} items")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result, ensure_ascii=False)
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