# 🛠️ 开发环境配置指南

## 📋 概述

本文档介绍如何设置一个干净高效的 Sehuatang 爬虫系统开发环境。

## 🏗️ 项目结构

```
sehuatang-crawler/
├── src/                          # 源代码目录
│   ├── backend/                  # 后端代码
│   │   ├── main.py              # 应用入口
│   │   ├── db.py                # 数据库配置
│   │   ├── models/              # 数据模型
│   │   ├── routes/              # API路由
│   │   ├── utils/               # 工具函数
│   │   └── requirements.txt     # Python依赖
│   └── frontend/                # 前端代码
│       ├── package.json         # Node.js依赖
│       ├── src/                 # React源码
│       └── public/              # 静态资源
├── docker/                       # Docker配置
│   ├── Dockerfile               # 生产环境镜像
│   ├── Dockerfile.dev           # 开发环境镜像
│   ├── docker-compose.yml       # 生产环境编排
│   ├── docker-compose.dev.yml   # 开发环境编排
│   └── init-db.sql             # 数据库初始化
├── scripts/                      # 管理脚本
│   ├── dev-start.ps1           # 开发环境启动
│   ├── deploy.sh               # 部署脚本
│   └── reorganize-project.ps1  # 项目重组
├── docs/                         # 文档
├── data/                         # 数据目录
└── logs/                         # 日志目录
```

## 🚀 快速开始

### 1. 项目重组（首次使用）

```powershell
# 运行项目重组脚本
.\scripts\reorganize-project.ps1
```

### 2. 开发环境启动

#### 方式一：Docker 开发环境（推荐）

```powershell
# 启动 Docker 开发环境
.\scripts\dev-start.ps1 docker

# 或者手动启动
cd docker
docker-compose -f docker-compose.dev.yml up -d
```

**访问地址：**
- 前端：http://localhost:3000
- 后端：http://localhost:8000
- API文档：http://localhost:8000/docs
- 数据库：localhost:5432

#### 方式二：本地开发环境

```powershell
# 启动本地开发环境
.\scripts\dev-start.ps1 local

# 或者手动启动
# 后端
cd src/backend
pip install -r requirements.txt
python main.py

# 前端（新终端）
cd src/frontend
npm install
npm start
```

## 🔧 开发工具配置

### VS Code 配置

创建 `.vscode/settings.json`：

```json
{
    "python.defaultInterpreterPath": "./src/backend/venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/node_modules": true
    },
    "search.exclude": {
        "**/data": true,
        "**/logs": true
    }
}
```

### 推荐的 VS Code 扩展

- Python
- Pylance
- Python Docstring Generator
- ES7+ React/Redux/React-Native snippets
- Prettier - Code formatter
- Docker

## 📝 开发工作流

### 1. 日常开发

```powershell
# 启动开发环境
.\scripts\dev-start.ps1 docker

# 查看日志
cd docker
docker-compose -f docker-compose.dev.yml logs -f

# 停止服务
docker-compose -f docker-compose.dev.yml down
```

### 2. 代码修改

- **后端代码**：修改 `src/backend/` 下的文件，自动重载
- **前端代码**：修改 `src/frontend/` 下的文件，自动重载
- **数据库**：修改 `docker/init-db.sql`，重启数据库容器

### 3. 依赖管理

```powershell
# 添加 Python 依赖
cd src/backend
pip install new-package
pip freeze > requirements.txt

# 添加 Node.js 依赖
cd src/frontend
npm install new-package
```

### 4. 数据库操作

```powershell
# 连接数据库
docker exec -it sehuatang-postgres-dev psql -U postgres -d sehuatang_db

# 重置数据库
cd docker
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

## 🐛 调试技巧

### 1. 后端调试

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或者使用日志
import logging
logging.debug("调试信息")
```

### 2. 前端调试

- 使用浏览器开发者工具
- 在代码中添加 `console.log()`
- 使用 React Developer Tools 扩展

### 3. 容器调试

```powershell
# 进入容器
docker exec -it sehuatang-backend-dev bash

# 查看容器日志
docker logs sehuatang-backend-dev

# 查看容器状态
docker ps
```

## 🔄 环境切换

### 开发环境 → 生产环境

```powershell
# 停止开发环境
cd docker
docker-compose -f docker-compose.dev.yml down

# 启动生产环境
docker-compose up -d
```

### 生产环境 → 开发环境

```powershell
# 停止生产环境
cd docker
docker-compose down

# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d
```

## 📊 性能优化

### 1. 开发环境优化

- 使用 Docker 卷挂载实现代码热重载
- 配置 `.dockerignore` 减少构建上下文
- 使用多阶段构建减少镜像大小

### 2. 代码优化

- 使用异步编程提高性能
- 实现数据库连接池
- 添加缓存机制

## 🚨 常见问题

### 1. 端口冲突

```powershell
# 查看端口占用
netstat -ano | findstr :8000

# 修改端口配置
# 编辑 docker/docker-compose.dev.yml
```

### 2. 数据库连接失败

```powershell
# 检查数据库状态
docker ps | findstr postgres

# 重启数据库
docker restart sehuatang-postgres-dev
```

### 3. 依赖安装失败

```powershell
# 清理缓存
docker system prune -f

# 重新构建镜像
docker-compose -f docker-compose.dev.yml build --no-cache
```

## 📚 相关文档

- [API 文档](API.md)
- [部署指南](DEPLOYMENT.md)
- [项目重组说明](REORGANIZATION.md)

---

**最后更新**：2025-08-29  
**版本**：1.0.0
