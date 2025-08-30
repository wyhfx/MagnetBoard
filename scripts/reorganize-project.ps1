# Sehuatang 爬虫系统项目重组脚本
# 将现有项目重新组织为更清晰的结构

Write-Host "🚀 开始重组 Sehuatang 爬虫系统项目结构..." -ForegroundColor Green

# 1. 移动后端文件到 src/backend
Write-Host "📁 移动后端文件..." -ForegroundColor Yellow
$backendFiles = @(
    "main.py",
    "db.py", 
    "downloader_manager.py",
    "models_settings.py",
    "new.py",
    "init_scheduler_table.py",
    "requirements.txt"
)

foreach ($file in $backendFiles) {
    if (Test-Path $file) {
        Move-Item $file "src/backend/" -Force
        Write-Host "  ✅ 移动 $file" -ForegroundColor Green
    }
}

# 移动后端目录
$backendDirs = @("models", "routes", "utils")
foreach ($dir in $backendDirs) {
    if (Test-Path $dir) {
        Move-Item $dir "src/backend/" -Force
        Write-Host "  ✅ 移动目录 $dir" -ForegroundColor Green
    }
}

# 2. 移动前端文件到 src/frontend
Write-Host "📁 移动前端文件..." -ForegroundColor Yellow
if (Test-Path "frontend") {
    Move-Item "frontend/*" "src/frontend/" -Force
    Remove-Item "frontend" -Force
    Write-Host "  ✅ 移动前端目录" -ForegroundColor Green
}

# 3. 移动 Docker 文件到 docker/
Write-Host "🐳 移动 Docker 文件..." -ForegroundColor Yellow
$dockerFiles = @(
    "Dockerfile",
    "docker-compose.yml",
    "init-db.sql",
    ".dockerignore"
)

foreach ($file in $dockerFiles) {
    if (Test-Path $file) {
        Move-Item $file "docker/" -Force
        Write-Host "  ✅ 移动 $file" -ForegroundColor Green
    }
}

# 4. 移动脚本文件到 scripts/
Write-Host "📜 移动脚本文件..." -ForegroundColor Yellow
$scriptFiles = @(
    "deploy.sh",
    "deploy.bat", 
    "start.sh",
    "start.bat",
    "stop.sh",
    "stop.bat",
    "build_simple.bat"
)

foreach ($file in $scriptFiles) {
    if (Test-Path $file) {
        Move-Item $file "scripts/" -Force
        Write-Host "  ✅ 移动 $file" -ForegroundColor Green
    }
}

# 5. 移动文档文件到 docs/
Write-Host "📚 移动文档文件..." -ForegroundColor Yellow
$docFiles = @(
    "README.md",
    "README_Docker.md",
    "DEPLOYMENT_SUCCESS.md"
)

foreach ($file in $docFiles) {
    if (Test-Path $file) {
        Move-Item $file "docs/" -Force
        Write-Host "  ✅ 移动 $file" -ForegroundColor Green
    }
}

# 6. 创建新的根目录文件
Write-Host "📝 创建新的根目录文件..." -ForegroundColor Yellow

# 创建新的 README.md
@"
# Sehuatang 爬虫系统

一个功能完整的爬虫管理系统，支持多种下载器集成和代理设置。

## 🚀 快速开始

### 使用 Docker（推荐）
\`\`\`bash
cd docker
docker-compose up -d
\`\`\`

访问: http://localhost:17500

### 开发环境
\`\`\`bash
# 后端开发
cd src/backend
pip install -r requirements.txt
python main.py

# 前端开发  
cd src/frontend
npm install
npm start
\`\`\`

## 📁 项目结构
- \`src/backend/\` - 后端代码
- \`src/frontend/\` - 前端代码
- \`docker/\` - Docker 配置
- \`scripts/\` - 部署脚本
- \`docs/\` - 文档

## 📚 详细文档
请查看 \`docs/\` 目录下的详细文档。
"@ | Out-File -FilePath "README.md" -Encoding UTF8

# 创建 .gitignore
@"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
data/
logs/
*.log
.env
.env.local

# Docker
.dockerignore
"@ | Out-File -FilePath ".gitignore" -Encoding UTF8

Write-Host "✅ 项目重组完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📁 新的项目结构：" -ForegroundColor Cyan
Write-Host "├── src/backend/     # 后端代码" -ForegroundColor White
Write-Host "├── src/frontend/    # 前端代码" -ForegroundColor White  
Write-Host "├── docker/          # Docker 配置" -ForegroundColor White
Write-Host "├── scripts/         # 部署脚本" -ForegroundColor White
Write-Host "├── docs/            # 文档" -ForegroundColor White
Write-Host "├── data/            # 数据目录" -ForegroundColor White
Write-Host "└── logs/            # 日志目录" -ForegroundColor White
Write-Host ""
Write-Host "🎯 下一步：" -ForegroundColor Yellow
Write-Host "1. 更新 docker/docker-compose.yml 中的路径" -ForegroundColor White
Write-Host "2. 测试 Docker 部署" -ForegroundColor White
Write-Host "3. 开始开发！" -ForegroundColor White
