# 📝 Serverless Todo Application

[日本語](./README.ja.md) | English

A full-stack serverless application built with AWS SAM and React.

## 🎯 Overview

A modern Todo application using AWS serverless architecture. Infrastructure is managed as code (IaC) and fully reproducible.

### Key Features

- ✅ Full CRUD operations (Create, Read, Update, Delete)
- ✅ User authentication & authorization (Amazon Cognito)
- ✅ Priority levels and due dates
- ✅ Task completion status management
- ✅ Responsive design

---

## 🏗️ Architecture

```
[User]
    ↓
[CloudFront] → [S3 (React App)]
    ↓
[API Gateway] → [Cognito Authorizer]
    ↓
[Lambda Functions (Python)]
    ↓
[DynamoDB]
```

### Tech Stack

#### Backend
- **Lambda**: Python 3.11
- **API Gateway**: REST API
- **DynamoDB**: NoSQL database (Single Table Design)
- **Cognito**: User authentication & management

#### Frontend
- **React**: 18.x
- **AWS Amplify**: Authentication SDK
- **S3**: Static hosting
- **CloudFront**: CDN distribution

#### IaC / DevOps
- **AWS SAM**: Infrastructure as Code
- **Docker**: Lambda build environment

---

## 🚀 Deployment

### Prerequisites

- AWS CLI v2
- SAM CLI
- Docker Desktop
- Node.js 18+
- Python 3.11+

### 1. Clone Repository

```bash
git clone https://github.com/jadebeach/serverless-todo.git
cd serverless-todo
```

### 2. Deploy Backend

```bash
# Build
sam build --use-container

# Deploy
sam deploy --guided
```

### 3. Deploy Frontend

```bash
# Install dependencies
cd frontend
npm install

# Build
npm run build

# Upload to S3
cd ..
./deploy-frontend.ps1
```

### 4. Access Application

```bash
# Get CloudFront URL
aws cloudformation describe-stacks \
  --stack-name serverless-todo-dev \
  --region ap-northeast-1 \
  --query "Stacks[0].Outputs[?OutputKey=='WebsiteURL'].OutputValue" \
  --output text
```

---

## 📁 Project Structure

```
serverless-todo/
├── template.yaml              # SAM template (IaC)
├── samconfig.toml            # SAM configuration
├── deploy-frontend.ps1       # Deployment script
├── functions/
│   ├── create_todo/          # Create task
│   ├── get_todos/            # List tasks
│   ├── update_todo/          # Update task
│   └── delete_todo/          # Delete task
└── frontend/
    ├── src/
    │   ├── components/       # React components
    │   ├── App.js
    │   └── aws-config.js     # AWS configuration
    └── package.json
```

---

## 🔧 Local Development

### Backend Local Testing

```bash
# Start API
sam local start-api

# Test in another terminal
curl -X POST http://localhost:3000/todos \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","dueDate":"2025-12-31T23:59:59Z","priority":"HIGH"}'
```

### Frontend Dev Server

```bash
cd frontend
npm start
# Opens at http://localhost:3000
```

---

## 🧪 API Endpoints

### Authentication

All endpoints require Cognito JWT authentication.

```
Authorization: Bearer {idToken}
```

### Endpoint List

| Method | Path | Description |
|--------|------|-------------|
| POST | `/todos` | Create task |
| GET | `/todos` | List tasks |
| PUT | `/todos/{taskId}` | Update task |
| DELETE | `/todos/{taskId}` | Delete task |

### Request Examples

**Create Task**
```json
POST /todos
{
  "title": "Shopping",
  "description": "Buy milk",
  "dueDate": "2025-12-01T10:00:00Z",
  "priority": "HIGH"
}
```

**List Tasks (with filters)**
```
GET /todos?status=PENDING&sortBy=dueDate&limit=20
```

---

## 📊 DynamoDB Table Design

### Single Table Design

```
PK: USER#{userId}
SK: TODO#{timestamp}#{taskId}

GSI1PK: USER#{userId}
GSI1SK: DUE#{dueDate}#{priority}
```

### Access Patterns

1. Get all user tasks → PK Query
2. Sort by due date → GSI1 Query
3. Get specific task → PK + SK Get
4. Update/Delete task → PK + SK Update/Delete

---

## 🔐 Security

- ✅ Authentication via Cognito User Pool
- ✅ JWT validation at API Gateway
- ✅ Per-user data isolation
- ✅ HTTPS communication (CloudFront)
- ✅ IAM Role least privilege principle

---

## 💰 Cost Estimation

For 1000 requests/month, 10 users:

- Lambda: ~$0.20
- API Gateway: ~$3.50
- DynamoDB: ~$0.25
- Cognito: Free tier
- S3 + CloudFront: ~$1.00
- **Total: ~$5/month**

※ After free tier

---

## 🎓 Learning Points

What you'll learn from this project:

### Infrastructure
- Serverless architecture design
- Infrastructure as Code with AWS SAM
- DynamoDB Single Table Design
- API Gateway configuration and CORS

### Backend
- Event-driven programming with Lambda
- DynamoDB Query/Scan operations
- JWT authentication implementation
- Error handling and logging

### Frontend
- React Hooks usage
- Authentication integration with AWS Amplify
- RESTful API consumption
- Responsive design

### DevOps
- CI/CD pipeline (manual)
- CloudFront cache management
- Environment variable management

---

## 🛠️ Troubleshooting

### CORS Errors

```bash
# Check CORS configuration in template.yaml
sam build --use-container
sam deploy
```

### Cognito Authentication Errors

```bash
# Verify User Pool Client settings
aws cognito-idp describe-user-pool-client \
  --user-pool-id {poolId} \
  --client-id {clientId}
```

### CloudFront 403 Errors

```bash
# Check S3 bucket policy
aws s3api get-bucket-policy --bucket {bucketName}
```

---

## 📈 Future Enhancements

- [ ] Social login (Google/Facebook)
- [ ] Task sharing features
- [ ] Real-time notifications (WebSocket)
- [ ] Task categories
- [ ] File attachments (S3)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring (CloudWatch Dashboards)
- [ ] Custom domain support

---

## 📄 License

MIT License

---

## 👤 Author

**Jade Beach**
- GitHub: [@jadebeach](https://github.com/jadebeach)

---

## 🙏 Acknowledgments

This project was created for learning AWS serverless architecture.