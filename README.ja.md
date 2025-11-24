## 🎯 プロジェクト概要

日本語 | [English](./README.md)

Amazon Web Services (AWS) のサーバーレスアーキテクチャを使用した、モダンなTodoアプリケーション。
インフラストラクチャはコード（IaC）で管理され、完全に再現可能。

### 主な機能

- ✅ タスクのCRUD操作（作成・読取・更新・削除）
- ✅ ユーザー認証・認可（Amazon Cognito）
- ✅ 優先度と期限の設定
- ✅ タスクの完了状態管理
- ✅ レスポンシブデザイン

---

## 🏗️ アーキテクチャ

```
[ユーザー]
    ↓
[CloudFront] → [S3 (React App)]
    ↓
[API Gateway] → [Cognito Authorizer]
    ↓
[Lambda Functions (Python)]
    ↓
[DynamoDB]
```

### 使用技術

#### バックエンド
- **Lambda**: Python 3.11
- **API Gateway**: REST API
- **DynamoDB**: NoSQL データベース（シングルテーブル設計）
- **Cognito**: ユーザー認証・管理

#### フロントエンド
- **React**: 18.x
- **AWS Amplify**: 認証SDK
- **S3**: 静的ホスティング
- **CloudFront**: CDN配信

#### IaC / DevOps
- **AWS SAM**: Infrastructure as Code
- **Docker**: Lambda関数のビルド環境

---

## 🚀 デプロイ方法

### 前提条件

- AWS CLI v2
- SAM CLI
- Docker Desktop
- Node.js 18+
- Python 3.11+

### 1. リポジトリのクローン

```bash
git clone https://github.com/jadebeach/serverless-todo.git
cd serverless-todo
```

### 2. バックエンドのデプロイ

```bash
# ビルド
sam build --use-container

# デプロイ
sam deploy --guided
```

### 3. フロントエンドのデプロイ

```bash
# Node.jsパッケージインストール
cd frontend
npm install

# ビルド
npm run build

# S3にアップロード
cd ..
./deploy-frontend.ps1
```

### 4. アクセス

```bash
# CloudFront URLを取得
aws cloudformation describe-stacks \
  --stack-name serverless-todo-dev \
  --region ap-northeast-1 \
  --query "Stacks[0].Outputs[?OutputKey=='WebsiteURL'].OutputValue" \
  --output text
```

---

## 📁 プロジェクト構造

```
serverless-todo/
├── template.yaml              # SAMテンプレート（IaC）
├── samconfig.toml            # SAM設定
├── deploy-frontend.ps1       # デプロイスクリプト
├── functions/
│   ├── create_todo/          # タスク作成
│   ├── get_todos/            # タスク一覧取得
│   ├── update_todo/          # タスク更新
│   └── delete_todo/          # タスク削除
└── frontend/
    ├── src/
    │   ├── components/       # Reactコンポーネント
    │   ├── App.js
    │   └── aws-config.js     # AWS設定
    └── package.json
```

---

## 🔧 ローカル開発

### バックエンドのローカルテスト

```bash
# API起動
sam local start-api

# 別ターミナルでテスト
curl -X POST http://localhost:3000/todos \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","dueDate":"2025-12-31T23:59:59Z","priority":"HIGH"}'
```

### フロントエンドの開発サーバー

```bash
cd frontend
npm start
# http://localhost:3000 で起動
```

---

## 🧪 API エンドポイント

### 認証

すべてのエンドポイントはCognito JWT認証が必要。

```
Authorization: Bearer {idToken}
```

### エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/todos` | タスク作成 |
| GET | `/todos` | タスク一覧取得 |
| PUT | `/todos/{taskId}` | タスク更新 |
| DELETE | `/todos/{taskId}` | タスク削除 |

### リクエスト例

**タスク作成**
```json
POST /todos
{
  "title": "買い物",
  "description": "牛乳を買う",
  "dueDate": "2025-12-01T10:00:00Z",
  "priority": "HIGH"
}
```

**タスク一覧取得（フィルタ）**
```
GET /todos?status=PENDING&sortBy=dueDate&limit=20
```

---

## 📊 DynamoDB テーブル設計

### シングルテーブル設計

```
PK: USER#{userId}
SK: TODO#{timestamp}#{taskId}

GSI1PK: USER#{userId}
GSI1SK: DUE#{dueDate}#{priority}
```

### アクセスパターン

1. ユーザーの全タスク取得 → PK Query
2. 期限順にソート → GSI1 Query
3. 特定タスク取得 → PK + SK Get
4. タスク更新/削除 → PK + SK Update/Delete

---

## 🔐 セキュリティ

- ✅ Cognito User Poolによる認証
- ✅ API GatewayでのJWT検証
- ✅ ユーザーごとのデータ分離
- ✅ HTTPS通信（CloudFront）
- ✅ IAM Roleによる最小権限の原則

---

## 💰 コスト概算

月間1000リクエスト、10ユーザーの場合：

- Lambda: ~$0.20
- API Gateway: ~$3.50
- DynamoDB: ~$0.25
- Cognito: 無料枠内
- S3 + CloudFront: ~$1.00
- **合計: 約 $5/月**

※ 無料枠適用後の概算

---

## 🎓 学習ポイント

このプロジェクトで学べること：

### インフラストラクチャ
- サーバーレスアーキテクチャの設計
- AWS SAMによるIaC
- DynamoDBのシングルテーブル設計
- API Gatewayの設定とCORS

### バックエンド
- Lambdaのイベント駆動プログラミング
- DynamoDBのQuery/Scan操作
- JWT認証の実装
- エラーハンドリングとロギング

### フロントエンド
- React Hooksの使用
- AWS Amplifyによる認証統合
- RESTful APIの呼び出し
- レスポンシブデザイン

### DevOps
- CI/CDパイプライン（手動）
- CloudFrontキャッシュ管理
- 環境変数の管理

---

## 🛠️ トラブルシューティング

### CORS エラー

```bash
# template.yamlのCORS設定を確認
sam build --use-container
sam deploy
```

### Cognito 認証エラー

```bash
# User Pool Client設定を確認
aws cognito-idp describe-user-pool-client \
  --user-pool-id {poolId} \
  --client-id {clientId}
```

### CloudFront 403エラー

```bash
# S3バケットポリシーを確認
aws s3api get-bucket-policy --bucket {bucketName}
```

---

## 📈 今後の拡張案

- [ ] ソーシャルログイン（Google/Facebook）
- [ ] タスクの共有機能
- [ ] リアルタイム通知（WebSocket）
- [ ] タスクのカテゴリ分類
- [ ] 添付ファイル対応（S3）
- [ ] CI/CDパイプライン（GitHub Actions）
- [ ] モニタリング（CloudWatch Dashboards）
- [ ] カスタムドメイン対応

---

## 📄 ライセンス

MIT License

---

## 👤 作成者

**Jade Beach**
- GitHub: [@jadebeach](https://github.com/jadebeach)

---

## 🙏 謝辞

このプロジェクトは、AWSサーバーレスアーキテクチャの学習を目的として作成されました。
