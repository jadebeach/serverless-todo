# Serverless Todo Application

AWS SAMを使ったサーバーレスTodoアプリケーション

## アーキテクチャ

- **Lambda**: Python 3.11
- **API Gateway**: REST API
- **DynamoDB**: シングルテーブル設計
- **IaC**: AWS SAM

## デプロイ方法
```bash
# ビルド
sam build --use-container

# デプロイ
sam deploy --guided
```

## API エンドポイント

### POST /todos
タスクを作成

**リクエストボディ**:
```json
{
  "title": "タスク名",
  "description": "説明（オプション）",
  "dueDate": "2025-12-31T23:59:59Z",
  "priority": "HIGH|MEDIUM|LOW"
}
```

## 開発環境

- Python 3.11+
- AWS SAM CLI
- Docker Desktop