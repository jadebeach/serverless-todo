# ========================================
# Configuration
# ========================================
$API_URL = "https://av8r75bzbj.execute-api.ap-northeast-1.amazonaws.com/Prod/todos"  # Replace with your URL

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Serverless Todo API Test" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# ========================================
# Test 1: POST - Create Task
# ========================================
Write-Host "`n[1/5] Testing POST (Create Task)..." -ForegroundColor Green

$body = @{
    title = "Test Task"
    description = "Testing all CRUD operations"
    dueDate = "2025-12-01T10:00:00Z"
    priority = "HIGH"
} | ConvertTo-Json

try {
    $createResult = Invoke-RestMethod -Uri $API_URL -Method Post -Body $body -ContentType "application/json"
    $taskId = $createResult.todo.taskId
    Write-Host "  ✓ Task created: $taskId" -ForegroundColor Green
    Write-Host "    Title: $($createResult.todo.title)" -ForegroundColor Gray
    Write-Host "    Priority: $($createResult.todo.priority)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ POST failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ========================================
# Test 2: GET - List All Tasks
# ========================================
Write-Host "`n[2/5] Testing GET (List Tasks)..." -ForegroundColor Green

try {
    $tasks = Invoke-RestMethod -Uri $API_URL -Method Get
    Write-Host "  ✓ Found $($tasks.count) task(s)" -ForegroundColor Green
    foreach ($task in $tasks.items) {
        Write-Host "    - $($task.title) [$($task.priority)]" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ✗ GET failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ========================================
# Test 3: GET with Filter
# ========================================
Write-Host "`n[3/5] Testing GET with status filter..." -ForegroundColor Green

try {
    $filtered = Invoke-RestMethod -Uri "${API_URL}?status=PENDING" -Method Get
    Write-Host "  ✓ Found $($filtered.count) PENDING task(s)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ GET with filter failed: $($_.Exception.Message)" -ForegroundColor Red
}

# ========================================
# Test 4: PUT - Update Task
# ========================================
Write-Host "`n[4/5] Testing PUT (Update Task)..." -ForegroundColor Green

$updateBody = @{
    title = "Updated Test Task"
    priority = "MEDIUM"
    status = "COMPLETED"
} | ConvertTo-Json

try {
    $updateResult = Invoke-RestMethod -Uri "${API_URL}/${taskId}" -Method Put -Body $updateBody -ContentType "application/json"
    Write-Host "  ✓ Task updated" -ForegroundColor Green
    Write-Host "    New Title: $($updateResult.task.title)" -ForegroundColor Gray
    Write-Host "    New Priority: $($updateResult.task.priority)" -ForegroundColor Gray
    Write-Host "    New Status: $($updateResult.task.status)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ PUT failed: $($_.Exception.Message)" -ForegroundColor Red
}

# ========================================
# Test 5: DELETE - Delete Task
# ========================================
Write-Host "`n[5/5] Testing DELETE (Delete Task)..." -ForegroundColor Green

try {
    $deleteResult = Invoke-RestMethod -Uri "${API_URL}/${taskId}" -Method Delete
    Write-Host "  ✓ Task deleted: $($deleteResult.taskId)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ DELETE failed: $($_.Exception.Message)" -ForegroundColor Red
}

# ========================================
# Verify Deletion
# ========================================
Write-Host "`n[Verify] Checking task was deleted..." -ForegroundColor Green

try {
    $verifyTasks = Invoke-RestMethod -Uri $API_URL -Method Get
    $stillExists = $verifyTasks.items | Where-Object { $_.taskId -eq $taskId }
    
    if ($stillExists) {
        Write-Host "  ✗ Task still exists!" -ForegroundColor Red
    } else {
        Write-Host "  ✓ Task successfully deleted" -ForegroundColor Green
    }
} catch {
    Write-Host "  ✗ Verification failed" -ForegroundColor Red
}

# ========================================
# Summary
# ========================================
Write-Host "`n==================================" -ForegroundColor Cyan
Write-Host "  All tests completed!" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan