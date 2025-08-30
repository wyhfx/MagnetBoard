# 开发环境启动脚本
param(
    [string]$Mode = "docker"  # docker 或 local
)

Write-Host "🚀 启动 Sehuatang 爬虫系统开发环境..." -ForegroundColor Green

if ($Mode -eq "docker") {
    Write-Host "🐳 使用 Docker 开发环境..." -ForegroundColor Yellow
    
    # 切换到 docker 目录
    Set-Location "docker"
    
    # 启动开发环境
    docker-compose -f docker-compose.dev.yml up -d
    
    Write-Host "✅ 开发环境启动完成！" -ForegroundColor Green
    Write-Host "📱 前端地址: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "🔧 后端地址: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "📚 API文档: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "🗄️ 数据库: localhost:5432" -ForegroundColor Cyan
    
} elseif ($Mode -eq "local") {
    Write-Host "💻 使用本地开发环境..." -ForegroundColor Yellow
    
    # 启动后端
    Write-Host "🔧 启动后端..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd src/backend; python main.py"
    
    # 启动前端
    Write-Host "📱 启动前端..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd src/frontend; npm start"
    
    Write-Host "✅ 本地开发环境启动完成！" -ForegroundColor Green
    Write-Host "📱 前端地址: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "🔧 后端地址: http://localhost:8000" -ForegroundColor Cyan
    
} else {
    Write-Host "❌ 无效的模式，请使用 'docker' 或 'local'" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎯 开发提示：" -ForegroundColor Yellow
Write-Host "- 代码修改会自动重载" -ForegroundColor White
Write-Host "- 查看日志: docker-compose logs -f" -ForegroundColor White
Write-Host "- 停止服务: docker-compose down" -ForegroundColor White
