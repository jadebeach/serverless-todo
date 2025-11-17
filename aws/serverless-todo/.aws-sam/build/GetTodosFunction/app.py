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
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body, ensure_ascii=False)
    }

def lambda_handler(event, context):
    """
    タスク一覧取得のLambdaハンドラ

    クエリパラメータ:
    - status: PENDING|COMPLETED (オプション)
    - limit: 取得件数（デフォルト20）
    - sortBy: createdAt|dueDate (デフォルトdueDate)
    - lastKey: ページネーション用（Base64エンコード済みJSON）
    """

    try:
        # クエリパラメータ取得
        params = event.get('queryStringParameters') or {}
        status_filter = params.get('status')
        limit = int(params.get('limit', 20))
        sort_by = params.get('sortBy', 'dueDate')

        # ユーザーID取得（後でCognitoから）
        user_id = 'test-user-001'

        # TODO: どのテーブル/インデックスを使うか決める
        # sortBy='dueDate'の場合はGSI1、'createdAt'の場合はメインテーブル

        if sort_by == 'dueDate':
            # GSI1を使って期限順に取得
            query_params = {
                'IndexName': 'GSI1',
                'KeyConditionExpression': Key('GSI1PK').eq(f'USER#{user_id}'),  # GSI1PKを指定
                'Limit': limit,
                'ScanIndexForward': True  # 昇順（期限が近い順）
            }
        else:
            # メインテーブルで作成日時順
            query_params = {
                'KeyConditionExpression': Key('PK').eq(f'USER#{user_id}'),  # PKを指定
                'Limit': limit,
                'ScanIndexForward': False  # 降順（登録が新しい順）
            }

        # ページネーション対応
        last_key = params.get('lastKey')
        if last_key:
            import base64
            # TODO: Base64デコードしてExclusiveStartKeyに設定
            decoded_key = json.loads(base64.b64decode(last_key))
            query_params['ExclusiveStartKey'] = decoded_key

        # DynamoDBクエリ実行
        response = table.query(**query_params)

        items = response.get('Items', [])

        # TODO: ステータスでフィルタリング（オプション）
        if status_filter:
            items = [item for item in items if item.get('status') == status_filter]

        # レスポンス用にDynamoDB内部キーを除外
        clean_items = []
        for item in items:
            clean_item = {
                'taskId': item['taskId'],
                'title': item['title'],
                'description': item.get('description', ''),
                'dueDate': item['dueDate'],
                'priority': item['priority'],
                'status': item['status'],
                'createdAt': item['createdAt'],
                'updatedAt': item['updatedAt']
            }
            clean_items.append(clean_item)

        # 次ページ用のキー
        result = {
            'items': clean_items,
            'count': len(clean_items)
        }

        # LastEvaluatedKeyがある場合（続きがある）
        if 'LastEvaluatedKey' in response:
            import base64
            # TODO: Base64エンコードしてレスポンスに含める
            next_key = base64.b64encode(
                json.dumps(response['LastEvaluatedKey']).encode()
            ).decode()
            result['nextKey'] = next_key

        return create_response(200, result)

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return create_response(500, {
            'error': 'Internal server error',
            'message': str(e)
        })