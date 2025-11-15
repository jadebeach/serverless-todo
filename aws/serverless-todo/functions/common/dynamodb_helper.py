import json
import os
import boto3
from datetime import datetime
from typing import Dict

# DynamoDBクライアント初期化
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def create_response(status_code: int, body: Dict) -> Dict:
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

def get_current_timestamp() -> str:
    """ISO8601形式のタイムスタンプを取得"""
    return datetime.utcnow().isoformat() + 'Z'

def build_pk(user_id: str) -> str:
    """Partition Keyを生成"""
    return f"USER#{user_id}"

def build_sk(task_id: str, created_at: str) -> str:
    """Sort Keyを生成"""
    return f"TODO#{created_at}#{task_id}"

def build_gsi1_sk(due_date: str, priority: str) -> str:
    """GSI1 Sort Keyを生成"""
    return f"DUE#{due_date}#{priority}"