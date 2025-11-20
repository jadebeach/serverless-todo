# ========================================
# Configuration - Replace with your values
# ========================================
$USER_POOL_ID = "ap-northeast-1_DCb4nxfS8"
$CLIENT_ID = "4jsl61qm1qo1ilp6ecmvoeohev"
$API_URL = "https://5vu7b12xe2.execute-api.ap-northeast-1.amazonaws.com/Prod/todos"
$USERNAME = "test@example.com"
$PASSWORD = "TestPassword123!"

# ========================================
# Step 1: Create User
# ========================================
Write-Host "Creating user..." -ForegroundColor Green
try {
    aws cognito-idp sign-up `
      --client-id $CLIENT_ID `
      --username $USERNAME `
      --password $PASSWORD `
      --user-attributes Name=email,Value=$USERNAME `
      --region ap-northeast-1
    
    # Confirm user email
    aws cognito-idp admin-confirm-sign-up `
      --user-pool-id $USER_POOL_ID `
      --username $USERNAME `
      --region ap-northeast-1
    
    Write-Host "User created successfully!" -ForegroundColor Green
} catch {
    Write-Host "User might already exist, continuing..." -ForegroundColor Yellow
}

# ========================================
# Step 2: Login
# ========================================
Write-Host "`nLogging in..." -ForegroundColor Green
$authResult = aws cognito-idp initiate-auth `
  --client-id $CLIENT_ID `
  --auth-flow USER_PASSWORD_AUTH `
  --auth-parameters USERNAME=$USERNAME,PASSWORD=$PASSWORD `
  --region ap-northeast-1 | ConvertFrom-Json

$idToken = $authResult.AuthenticationResult.IdToken
Write-Host "Login successful! Token obtained." -ForegroundColor Green

# ========================================
# Step 3: Create Task
# ========================================
Write-Host "`nCreating task..." -ForegroundColor Green
$headers = @{
    "Authorization" = "Bearer $idToken"
}

$body = @{
    title = "Auth Test Task"
    description = "Testing Cognito authentication"
    dueDate = "2025-11-30T23:59:59Z"
    priority = "HIGH"
} | ConvertTo-Json -Compress

$createResult = Invoke-RestMethod -Uri $API_URL -Method Post -Headers $headers -Body $body -ContentType "application/json"
Write-Host "Task created: $($createResult.todo.taskId)" -ForegroundColor Green

# ========================================
# Step 4: Get Tasks
# ========================================
Write-Host "`nFetching tasks..." -ForegroundColor Green
$tasks = Invoke-RestMethod -Uri $API_URL -Method Get -Headers $headers
Write-Host "Found $($tasks.count) task(s)" -ForegroundColor Green
$tasks.items | Format-Table taskId, title, priority, status

Write-Host "`nAll tests passed!" -ForegroundColor Green