# cleanup-for-release.ps1 - 清理项目文件，准备发布

Write-Host "🧹 开始清理项目文件..." -ForegroundColor Green
Write-Host ""

# 1. 停止所有Docker容器
Write-Host "🛑 停止所有Docker容器..." -ForegroundColor Yellow
docker-compose -f docker-compose.dev.yml down 2>$null
docker-compose -f docker-compose.prod.yml down 2>$null
Write-Host "✓ Docker容器已停止" -ForegroundColor Green

# 2. 删除临时文件和目录
Write-Host ""
Write-Host "🗑️ 删除临时文件和目录..." -ForegroundColor Yellow

$tempFiles = @(
    "test_*.ps1",
    "test_*.bat",
    "download_packages.bat",
    "restore_original_theme.bat",
    "start_dev.bat",
    "stop_dev.bat",
    "rebuild_dev.bat",
    "check_dev_status.bat",
    "logs_dev.bat",
    "test_playwright.bat",
    "test_dev_environment.bat",
    "test_final_system.bat",
    "test_realtime_logs.bat",
    "test_realtime_logs.ps1",
    "test_concurrent_setting.ps1",
    "test_frontend_status.ps1",
    "test_theme_switch.ps1",
    "test_log_format.ps1",
    "test_final_system.ps1",
    "DEPLOYMENT_SUCCESS.md",
    "README_DOCKER_DEV.md"
)

$tempDirs = @(
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "node_modules",
    "frontend/node_modules",
    "docker/python_cache",
    "downloaded_images",
    "logs",
    "data"
)

# 删除临时文件
foreach ($file in $tempFiles) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "  删除: $file" -ForegroundColor Gray
    }
}

# 删除临时目录
foreach ($dir in $tempDirs) {
    if (Test-Path $dir) {
        Remove-Item $dir -Recurse -Force
        Write-Host "  删除目录: $dir" -ForegroundColor Gray
    }
}

Write-Host "✓ 临时文件清理完成" -ForegroundColor Green

# 3. 保留必要的文件
Write-Host ""
Write-Host "📋 保留的核心文件:" -ForegroundColor Yellow
$coreFiles = @(
    "main.py",
    "db.py",
    "requirements.txt",
    "init-db.sql",
    "Dockerfile.prod",
    "docker-compose.prod.yml",
    "build-and-deploy.ps1",
    "cleanup-for-release.ps1",
    "models_*.py",
    "routes/",
    "utils/",
    "frontend/src/",
    "frontend/public/",
    "frontend/package.json",
    "frontend/tailwind.config.js",
    "frontend/tsconfig.json",
    "frontend/postcss.config.js",
    "new.py",
    "new_crawler_manager.py",
    "downloader_manager.py",
    "scheduler_manager.py",
    "settings_manager.py",
    "cache_manager.py",
    "collect_cookies.py",
    "simple_qr_login.py",
    "init_scheduler_table.py",
    "migrate_settings_table.py",
    "init_postgresql.py",
    "watch_and_build.py",
    ".gitignore",
    "env.example"
)

foreach ($file in $coreFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    }
}

# 4. 创建发布说明
Write-Host ""
Write-Host "📝 创建发布说明..." -ForegroundColor Yellow
$releaseNotes = @"
# Sehuatang 爬虫系统 v1.0.0

## 🎉 新功能
- 前后端合一部署，单端口访问
- 苹果风格UI设计，支持主题切换
- 实时爬虫日志和状态监控
- 智能代理配置和cookies管理
- 数据总览和批量操作
- 定时任务调度系统

## 🚀 快速部署
1. 构建镜像: `docker build -f Dockerfile.prod -t sehuatang-app:latest .`
2. 启动服务: `docker-compose -f docker-compose.prod.yml up -d`
3. 访问应用: http://localhost:8000

## 📋 系统要求
- Docker 20.10+
- Docker Compose 2.0+
- 至少2GB内存
- 至少10GB存储空间

## 🔧 配置说明
- 数据库: PostgreSQL 15
- 后端: FastAPI + Python 3.11
- 前端: React + TypeScript + Tailwind CSS
- 爬虫: Playwright + 代理支持

## 📁 数据持久化
- 数据库: `postgres_data` 卷
- 应用数据: `./data` 目录
- 日志文件: `./logs` 目录

## 🛠️ 管理命令
- 查看日志: `docker-compose -f docker-compose.prod.yml logs -f`
- 停止服务: `docker-compose -f docker-compose.prod.yml down`
- 重启服务: `docker-compose -f docker-compose.prod.yml restart`

## 🔒 安全说明
- 生产环境请修改默认密码
- 建议配置反向代理和SSL
- 定期备份数据库

## 📞 技术支持
如有问题，请查看日志文件或联系开发者。
"@

$releaseNotes | Out-File -FilePath "RELEASE_NOTES.md" -Encoding UTF8
Write-Host "✓ 发布说明已创建: RELEASE_NOTES.md" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 项目清理完成！" -ForegroundColor Green
Write-Host "📦 现在可以构建生产版本了" -ForegroundColor Cyan
Write-Host ""
Read-Host "按 Enter 键继续"
