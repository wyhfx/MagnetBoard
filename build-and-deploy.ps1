# build-and-deploy.ps1 - 构建和部署前后端合一版本

Write-Host "🚀 开始构建前后端合一版本..." -ForegroundColor Green
Write-Host ""

# 1. 检查前端构建
Write-Host "📦 检查前端构建..." -ForegroundColor Yellow
if (Test-Path "frontend/build") {
    Write-Host "✓ 前端构建目录已存在" -ForegroundColor Green
} else {
    Write-Host "⚠️ 前端构建目录不存在，开始构建..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    npm run build
    Set-Location ..
    Write-Host "✓ 前端构建完成" -ForegroundColor Green
}

# 2. 停止开发环境
Write-Host ""
Write-Host "🛑 停止开发环境..." -ForegroundColor Yellow
docker-compose -f docker-compose.dev.yml down
Write-Host "✓ 开发环境已停止" -ForegroundColor Green

# 3. 构建生产镜像
Write-Host ""
Write-Host "🐳 构建生产Docker镜像..." -ForegroundColor Yellow
docker build -f Dockerfile.prod -t sehuatang-app:latest .
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker镜像构建成功" -ForegroundColor Green
} else {
    Write-Host "✗ Docker镜像构建失败" -ForegroundColor Red
    exit 1
}

# 4. 启动生产环境
Write-Host ""
Write-Host "🚀 启动生产环境..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 生产环境启动成功" -ForegroundColor Green
} else {
    Write-Host "✗ 生产环境启动失败" -ForegroundColor Red
    exit 1
}

# 5. 等待服务启动
Write-Host ""
Write-Host "⏳ 等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 6. 检查服务状态
Write-Host ""
Write-Host "🔍 检查服务状态..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ 应用服务运行正常" -ForegroundColor Green
    } else {
        Write-Host "⚠️ 应用服务响应异常: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ 应用服务检查失败: $($_.Exception.Message)" -ForegroundColor Yellow
}

# 7. 显示访问信息
Write-Host ""
Write-Host "🎉 部署完成！" -ForegroundColor Green
Write-Host "🌐 访问地址: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API文档: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 管理命令:" -ForegroundColor Yellow
Write-Host "  查看日志: docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor White
Write-Host "  停止服务: docker-compose -f docker-compose.prod.yml down" -ForegroundColor White
Write-Host "  重启服务: docker-compose -f docker-compose.prod.yml restart" -ForegroundColor White
Write-Host ""
Read-Host "按 Enter 键继续"
