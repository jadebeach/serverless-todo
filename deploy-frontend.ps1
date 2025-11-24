# ========================================
# Frontend Deployment Script
# ========================================

$STACK_NAME = "serverless-todo-dev"
$REGION = "ap-northeast-1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deploying Serverless Todo Frontend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ========================================
# Step 1: Deploy Infrastructure
# ========================================
Write-Host "`n[1/5] Deploying infrastructure..." -ForegroundColor Green

sam build --use-container
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

sam deploy
if ($LASTEXITCODE -ne 0) {
    Write-Host "Deploy failed!" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Infrastructure deployed" -ForegroundColor Green

# ========================================
# Step 2: Get Stack Outputs
# ========================================
Write-Host "`n[2/5] Getting stack outputs..." -ForegroundColor Green

$outputs = aws cloudformation describe-stacks `
  --stack-name $STACK_NAME `
  --region $REGION `
  --query "Stacks[0].Outputs" | ConvertFrom-Json

$bucketName = ($outputs | Where-Object { $_.OutputKey -eq "FrontendBucketName" }).OutputValue
$cloudFrontUrl = ($outputs | Where-Object { $_.OutputKey -eq "CloudFrontURL" }).OutputValue
$apiUrl = ($outputs | Where-Object { $_.OutputKey -eq "ApiUrl" }).OutputValue
$userPoolId = ($outputs | Where-Object { $_.OutputKey -eq "UserPoolId" }).OutputValue
$clientId = ($outputs | Where-Object { $_.OutputKey -eq "UserPoolClientId" }).OutputValue

Write-Host "  Bucket: $bucketName" -ForegroundColor Gray
Write-Host "  CloudFront: $cloudFrontUrl" -ForegroundColor Gray
Write-Host "  API: $apiUrl" -ForegroundColor Gray

# ========================================
# Step 3: Update Frontend Config
# ========================================
Write-Host "`n[3/5] Updating frontend configuration..." -ForegroundColor Green

$configContent = @"
// AWS Cognito and API Gateway configuration
const awsConfig = {
  // Cognito Settings
  Auth: {
    Cognito: {
      region: '$REGION',
      userPoolId: '$userPoolId',
      userPoolClientId: '$clientId',
    }
  },
  
  // API Gateway Settings
  API: {
    REST: {
      'TodoAPI': {
        endpoint: '$apiUrl'.replace(/\/$/, ''),
        region: '$REGION'
      }
    }
  }
};

export default awsConfig;
"@

$configContent | Out-File -FilePath "frontend\src\aws-config.js" -Encoding UTF8
Write-Host "  ✓ Configuration updated" -ForegroundColor Green

# ========================================
# Step 4: Build Frontend
# ========================================
Write-Host "`n[4/5] Building React app..." -ForegroundColor Green

cd frontend
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    cd ..
    exit 1
}
cd ..

Write-Host "  ✓ Build completed" -ForegroundColor Green

# ========================================
# Step 5: Upload to S3
# ========================================
Write-Host "`n[5/5] Uploading to S3..." -ForegroundColor Green

aws s3 sync frontend\build s3://$bucketName --delete --region $REGION
if ($LASTEXITCODE -ne 0) {
    Write-Host "Upload failed!" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Files uploaded" -ForegroundColor Green

# ========================================
# Step 6: Invalidate CloudFront Cache
# ========================================
Write-Host "`n[6/5] Invalidating CloudFront cache..." -ForegroundColor Green

$distributionId = aws cloudfront list-distributions `
  --query "DistributionList.Items[?contains(Origins.Items[0].DomainName, '$bucketName')].Id" `
  --output text

if ($distributionId) {
    aws cloudfront create-invalidation `
      --distribution-id $distributionId `
      --paths "/*" | Out-Null
    Write-Host "  ✓ Cache invalidated" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Could not find CloudFront distribution" -ForegroundColor Yellow
}

# ========================================
# Summary
# ========================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nYour app is now live at:" -ForegroundColor Green
Write-Host "  https://$cloudFrontUrl" -ForegroundColor Cyan
Write-Host "`nAPI Endpoint:" -ForegroundColor Green
Write-Host "  $apiUrl" -ForegroundColor Gray
Write-Host "`nS3 Bucket:" -ForegroundColor Green
Write-Host "  $bucketName" -ForegroundColor Gray
Write-Host ""