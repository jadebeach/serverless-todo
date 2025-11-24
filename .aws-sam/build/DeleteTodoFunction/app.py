import json
import os
import boto3
from boto3.dynamodb.conditions import Key

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
    """タスク削除"""
    
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
        
        print(f"Delete taskId={task_id}")
        
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
        
        # DynamoDB削除
        table.delete_item(
            Key={
                'PK': existing_task['PK'],
                'SK': existing_task['SK']
            }
        )
        
        print("Delete successful!")
        
        # レスポンス
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Task deleted successfully',
                'taskId': task_id
            })
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