# push-to-repos.ps1 - 推送到GitHub和Docker Hub

param(
    [Parameter(Mandatory=$true)]
    [string]$DockerHubUsername,
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "1.0.0"
)

Write-Host "🚀 开始推送到GitHub和Docker Hub..." -ForegroundColor Green
Write-Host ""

# 1. 检查Git状态
Write-Host "📋 检查Git状态..." -ForegroundColor Yellow
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "⚠️ 发现未提交的更改:" -ForegroundColor Yellow
    $gitStatus | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    Write-Host ""
    $confirm = Read-Host "是否继续提交这些更改? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "❌ 操作已取消" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ 工作目录干净" -ForegroundColor Green
}

# 2. 添加文件到Git
Write-Host ""
Write-Host "📦 添加文件到Git..." -ForegroundColor Yellow
git add .
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 文件已添加到Git" -ForegroundColor Green
} else {
    Write-Host "✗ Git添加失败" -ForegroundColor Red
    exit 1
}

# 3. 提交更改
Write-Host ""
Write-Host "💾 提交更改..." -ForegroundColor Yellow
$commitMessage = "Release v$Version - 前后端合一部署版本"
git commit -m $commitMessage
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 更改已提交" -ForegroundColor Green
} else {
    Write-Host "✗ Git提交失败" -ForegroundColor Red
    exit 1
}

# 4. 创建标签
Write-Host ""
Write-Host "🏷️ 创建版本标签..." -ForegroundColor Yellow
git tag -a "v$Version" -m "Release v$Version"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 版本标签已创建: v$Version" -ForegroundColor Green
} else {
    Write-Host "✗ 标签创建失败" -ForegroundColor Red
    exit 1
}

# 5. 推送到GitHub
Write-Host ""
Write-Host "📤 推送到GitHub..." -ForegroundColor Yellow
git push origin main
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 代码已推送到GitHub" -ForegroundColor Green
} else {
    Write-Host "⚠️ GitHub推送失败，请检查远程仓库配置" -ForegroundColor Yellow
}

git push origin "v$Version"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 标签已推送到GitHub" -ForegroundColor Green
} else {
    Write-Host "⚠️ 标签推送失败" -ForegroundColor Yellow
}

# 6. 构建Docker镜像
Write-Host ""
Write-Host "🐳 构建Docker镜像..." -ForegroundColor Yellow
$imageName = "$DockerHubUsername/sehuatang-app"
$taggedImage = "$imageName`:$Version"
$latestImage = "$imageName`:latest"

docker build -f Dockerfile.prod -t $taggedImage -t $latestImage .
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker镜像构建成功" -ForegroundColor Green
} else {
    Write-Host "✗ Docker镜像构建失败" -ForegroundColor Red
    exit 1
}

# 7. 推送到Docker Hub
Write-Host ""
Write-Host "📤 推送到Docker Hub..." -ForegroundColor Yellow

# 推送版本标签
docker push $taggedImage
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 版本镜像已推送到Docker Hub: $taggedImage" -ForegroundColor Green
} else {
    Write-Host "✗ 版本镜像推送失败" -ForegroundColor Red
    exit 1
}

# 推送latest标签
docker push $latestImage
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Latest镜像已推送到Docker Hub: $latestImage" -ForegroundColor Green
} else {
    Write-Host "✗ Latest镜像推送失败" -ForegroundColor Red
    exit 1
}

# 8. 创建部署说明
Write-Host ""
Write-Host "📝 创建部署说明..." -ForegroundColor Yellow
$deployInstructions = @"
# Sehuatang 爬虫系统 v$Version 部署说明

## 🐳 Docker Hub 镜像
- 版本镜像: `$taggedImage`
- 最新镜像: `$latestImage`

## 🚀 快速部署
```bash
# 拉取镜像
docker pull $latestImage

# 创建docker-compose.yml
version: '3.8'
services:
  sehuatang-app:
    image: $latestImage
    container_name: sehuatang-app
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
      - DATABASE_NAME=sehuatang_db
      - DATABASE_USER=postgres
      - DATABASE_PASSWORD=sehuatang123
      - APP_HOST=0.0.0.0
      - APP_PORT=8000
      - APP_RELOAD=false
      - DEBUG=false
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - postgres

  postgres:
    image: postgres:15-alpine
    container_name: sehuatang-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=sehuatang_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=sehuatang123
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:

# 启动服务
docker-compose up -d
```

## 🌐 访问地址
- 应用界面: http://localhost:8000
- API文档: http://localhost:8000/docs

## 📋 系统要求
- Docker 20.10+
- Docker Compose 2.0+
- 至少2GB内存
- 至少10GB存储空间

## 🔧 配置说明
- 单端口部署，前后端合一
- 支持苹果风格UI主题切换
- 实时爬虫日志和状态监控
- 智能代理配置和cookies管理
- 数据总览和批量操作
- 定时任务调度系统

## 🛠️ 管理命令
- 查看日志: `docker-compose logs -f sehuatang-app`
- 停止服务: `docker-compose down`
- 重启服务: `docker-compose restart`
- 更新镜像: `docker-compose pull && docker-compose up -d`

## 🔒 安全建议
- 生产环境请修改默认密码
- 建议配置反向代理和SSL
- 定期备份数据库
- 限制容器资源使用

## 📞 技术支持
- GitHub: [项目地址]
- 版本: v$Version
- 发布时间: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
"@

$deployInstructions | Out-File -FilePath "DEPLOYMENT_INSTRUCTIONS.md" -Encoding UTF8
Write-Host "✓ 部署说明已创建: DEPLOYMENT_INSTRUCTIONS.md" -ForegroundColor Green

# 9. 显示成功信息
Write-Host ""
Write-Host "🎉 推送完成！" -ForegroundColor Green
Write-Host "📦 版本: v$Version" -ForegroundColor Cyan
Write-Host "🐳 Docker Hub: $latestImage" -ForegroundColor Cyan
Write-Host "📚 部署说明: DEPLOYMENT_INSTRUCTIONS.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 下一步操作:" -ForegroundColor Yellow
Write-Host "  1. 在Docker Hub上验证镜像" -ForegroundColor White
Write-Host "  2. 在GitHub上创建Release" -ForegroundColor White
Write-Host "  3. 分享部署说明给用户" -ForegroundColor White
Write-Host ""
Read-Host "按 Enter 键继续"
