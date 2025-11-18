import json
import os
import boto3
from boto3.dynamodb.conditions import Key

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
    """タスク削除のLambdaハンドラ"""
    
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # パスパラメータからtaskId取得
        path_params = event.get('pathParameters', {})
        task_id = path_params.get('taskId')
        
        if not task_id:
            return create_response(400, {'error': 'taskId is required'})
        
        print(f"Delete request for taskId={task_id}")
        
        # ユーザーID取得（後でCognitoから）
        user_id = 'test-user-001'
        
        # タスクを検索
        existing_task = find_task_by_id(user_id, task_id)
        
        if not existing_task:
            return create_response(404, {
                'error': 'Task not found',
                'taskId': task_id
            })
        
        print(f"Found task: PK={existing_task['PK']}, SK={existing_task['SK']}")
        
        # DynamoDBから削除
        table.delete_item(
            Key={
                'PK': existing_task['PK'],
                'SK': existing_task['SK']
            }
        )
        
        print(f"Successfully deleted task: {task_id}")
        
        return create_response(200, {
            'message': 'Task deleted successfully',
            'taskId': task_id
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return create_response(500, {
            'error': 'Internal server error',
            'message': str(e)
        })
