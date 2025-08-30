# release-pipeline.ps1 - 完整发布流程

param(
    [Parameter(Mandatory=$true)]
    [string]$DockerHubUsername,
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "1.0.0"
)

Write-Host "🚀 Sehuatang 爬虫系统发布流程 v$Version" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# 1. 项目清理
Write-Host "📋 步骤 1: 项目清理" -ForegroundColor Yellow
Write-Host "执行项目清理脚本..." -ForegroundColor Gray
& .\cleanup-for-release.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 项目清理失败" -ForegroundColor Red
    exit 1
}
Write-Host "✓ 项目清理完成" -ForegroundColor Green
Write-Host ""

# 2. 构建生产版本
Write-Host "📋 步骤 2: 构建生产版本" -ForegroundColor Yellow
Write-Host "执行构建和部署脚本..." -ForegroundColor Gray
& .\build-and-deploy.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 生产版本构建失败" -ForegroundColor Red
    exit 1
}
Write-Host "✓ 生产版本构建完成" -ForegroundColor Green
Write-Host ""

# 3. 推送到仓库
Write-Host "📋 步骤 3: 推送到仓库" -ForegroundColor Yellow
Write-Host "执行推送脚本..." -ForegroundColor Gray
& .\push-to-repos.ps1 -DockerHubUsername $DockerHubUsername -Version $Version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 推送失败" -ForegroundColor Red
    exit 1
}
Write-Host "✓ 推送完成" -ForegroundColor Green
Write-Host ""

# 4. 创建发布总结
Write-Host "📋 步骤 4: 创建发布总结" -ForegroundColor Yellow
$releaseSummary = @"
# Sehuatang 爬虫系统 v$Version 发布总结

## 🎉 发布信息
- **版本**: v$Version
- **发布时间**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- **Docker Hub**: $DockerHubUsername/sehuatang-app
- **部署方式**: 前后端合一，单端口部署

## ✨ 主要特性
- 🎨 苹果风格UI设计，支持主题切换
- 🚀 前后端合一部署，简化NAS部署
- 📊 实时爬虫日志和状态监控
- 🔧 智能代理配置和cookies管理
- 📋 数据总览和批量操作
- ⏰ 定时任务调度系统
- 🎯 单端口访问，适合NAS环境

## 🛠️ 技术栈
- **后端**: FastAPI + Python 3.11 + PostgreSQL
- **前端**: React + TypeScript + Tailwind CSS
- **爬虫**: Playwright + 代理支持
- **部署**: Docker + Docker Compose

## 📦 部署方式
1. **Docker Hub镜像**: `docker pull $DockerHubUsername/sehuatang-app:latest`
2. **本地构建**: `docker build -f Dockerfile.prod -t sehuatang-app:latest .`
3. **一键部署**: `docker-compose -f docker-compose.prod.yml up -d`

## 🌐 访问地址
- **应用界面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📋 系统要求
- Docker 20.10+
- Docker Compose 2.0+
- 至少2GB内存
- 至少10GB存储空间

## 🔒 安全特性
- 非root用户运行
- 数据持久化存储
- 环境变量配置
- 健康检查接口

## 📁 文件结构
```
sehuatang-app/
├── main.py                 # 主应用入口
├── db.py                   # 数据库配置
├── requirements.txt        # Python依赖
├── Dockerfile.prod         # 生产环境Dockerfile
├── docker-compose.prod.yml # 生产环境配置
├── frontend/               # 前端源码
│   ├── src/               # React源码
│   ├── public/            # 静态资源
│   └── package.json       # 前端依赖
├── routes/                # API路由
├── models_*.py            # 数据模型
├── data/                  # 应用数据
└── logs/                  # 日志文件
```

## 🚀 快速开始
```bash
# 1. 拉取镜像
docker pull $DockerHubUsername/sehuatang-app:latest

# 2. 创建docker-compose.yml
version: '3.8'
services:
  sehuatang-app:
    image: $DockerHubUsername/sehuatang-app:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_HOST=postgres
      - DATABASE_PASSWORD=sehuatang123
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - postgres

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=sehuatang_db
      - POSTGRES_PASSWORD=sehuatang123
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:

# 3. 启动服务
docker-compose up -d
```

## 🛠️ 管理命令
- **查看日志**: `docker-compose logs -f sehuatang-app`
- **停止服务**: `docker-compose down`
- **重启服务**: `docker-compose restart`
- **更新镜像**: `docker-compose pull && docker-compose up -d`
- **备份数据**: `docker-compose exec postgres pg_dump -U postgres sehuatang_db > backup.sql`

## 🔧 配置说明
- **数据库**: PostgreSQL 15，支持UTF-8编码
- **时区**: 自动设置为北京时间
- **代理**: 支持HTTP/HTTPS代理配置
- **日志**: 实时日志流，支持SSE
- **主题**: 苹果风格和经典风格切换

## 📞 技术支持
- **GitHub**: [项目地址]
- **Docker Hub**: https://hub.docker.com/r/$DockerHubUsername/sehuatang-app
- **版本**: v$Version
- **文档**: http://localhost:8000/docs

## 🔄 更新日志
### v$Version
- 🎉 首次发布
- 🎨 苹果风格UI设计
- 🚀 前后端合一部署
- 📊 实时监控和日志
- 🔧 智能代理配置
- 📋 数据管理和操作
- ⏰ 定时任务系统

---
*Sehuatang 爬虫系统 - 强大的磁力链接管理和元数据获取工具*
"@

$releaseSummary | Out-File -FilePath "RELEASE_SUMMARY.md" -Encoding UTF8
Write-Host "✓ 发布总结已创建: RELEASE_SUMMARY.md" -ForegroundColor Green

# 5. 显示最终结果
Write-Host ""
Write-Host "🎉 发布流程完成！" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "📦 版本: v$Version" -ForegroundColor Cyan
Write-Host "🐳 Docker Hub: $DockerHubUsername/sehuatang-app" -ForegroundColor Cyan
Write-Host "🌐 访问地址: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 生成的文件:" -ForegroundColor Yellow
Write-Host "  ✓ RELEASE_NOTES.md - 发布说明" -ForegroundColor Green
Write-Host "  ✓ DEPLOYMENT_INSTRUCTIONS.md - 部署说明" -ForegroundColor Green
Write-Host "  ✓ RELEASE_SUMMARY.md - 发布总结" -ForegroundColor Green
Write-Host ""
Write-Host "📋 下一步操作:" -ForegroundColor Yellow
Write-Host "  1. 在Docker Hub上验证镜像" -ForegroundColor White
Write-Host "  2. 在GitHub上创建Release" -ForegroundColor White
Write-Host "  3. 分享部署说明给用户" -ForegroundColor White
Write-Host "  4. 监控部署反馈" -ForegroundColor White
Write-Host ""
Write-Host "🎯 发布成功！你的Sehuatang爬虫系统已经准备好部署到任何NAS环境了！" -ForegroundColor Green
Write-Host ""
Read-Host "按 Enter 键继续"
