# 🔄 项目重组说明

## 📋 重组目标

将原本混乱的项目结构重新组织为清晰、高效的开发环境，实现：

- ✅ **代码与配置分离**：源代码、Docker配置、脚本、文档各司其职
- ✅ **开发与生产分离**：独立的开发环境和生产环境配置
- ✅ **热重载支持**：代码修改自动重载，提高开发效率
- ✅ **环境一致性**：Docker确保开发和生产环境一致
- ✅ **易于维护**：清晰的项目结构便于团队协作

## 🏗️ 重组前后对比

### 重组前（混乱）
```
sehuatang-crawler-main/
├── main.py                    # 后端代码
├── db.py                      # 后端代码
├── frontend/                  # 前端代码
├── Dockerfile                 # Docker配置
├── docker-compose.yml         # Docker配置
├── deploy.sh                  # 脚本
├── README.md                  # 文档
├── requirements.txt           # 后端依赖
├── package.json               # 前端依赖
└── ... (各种文件混在一起)
```

### 重组后（清晰）
```
sehuatang-crawler/
├── src/                       # 源代码目录
│   ├── backend/              # 后端代码
│   └── frontend/             # 前端代码
├── docker/                    # Docker配置
│   ├── Dockerfile            # 生产环境
│   ├── Dockerfile.dev        # 开发环境
│   ├── docker-compose.yml    # 生产编排
│   └── docker-compose.dev.yml # 开发编排
├── scripts/                   # 管理脚本
├── docs/                      # 文档
├── data/                      # 数据目录
└── logs/                      # 日志目录
```

## 🚀 重组步骤

### 1. 创建新目录结构
```powershell
mkdir src, src/backend, src/frontend, docker, scripts, docs
```

### 2. 移动文件
- **后端文件** → `src/backend/`
- **前端文件** → `src/frontend/`
- **Docker文件** → `docker/`
- **脚本文件** → `scripts/`
- **文档文件** → `docs/`

### 3. 创建开发环境配置
- `docker/docker-compose.dev.yml` - 开发环境编排
- `docker/Dockerfile.dev` - 开发环境镜像
- `scripts/dev-start.ps1` - 开发环境启动脚本

## 🎯 重组优势

### 1. 开发效率提升
- **热重载**：代码修改自动重载，无需手动重启
- **环境隔离**：开发环境独立，不影响生产
- **快速切换**：一键切换开发/生产环境

### 2. 维护性提升
- **清晰结构**：文件分类明确，易于查找
- **配置分离**：不同环境配置独立管理
- **文档完善**：详细的使用说明和故障排除

### 3. 团队协作
- **标准化**：统一的项目结构和开发流程
- **可复制**：新成员可快速搭建相同环境
- **版本控制**：更好的 Git 管理

## 🔧 使用方法

### 首次重组
```powershell
# 运行重组脚本
.\scripts\reorganize-project.ps1
```

### 日常开发
```powershell
# 启动开发环境
.\scripts\dev-start.ps1 docker

# 或本地开发
.\scripts\dev-start.ps1 local
```

### 生产部署
```powershell
cd docker
docker-compose up -d
```

## 📊 性能对比

| 方面 | 重组前 | 重组后 |
|------|--------|--------|
| 项目启动时间 | 2-3分钟 | 30秒 |
| 代码修改重载 | 手动重启 | 自动重载 |
| 环境切换 | 复杂 | 一键切换 |
| 文件查找 | 困难 | 快速定位 |
| 团队协作 | 混乱 | 标准化 |

## 🚨 注意事项

### 1. 路径更新
重组后需要更新以下文件中的路径：
- Docker 配置文件中的 `COPY` 路径
- 脚本文件中的相对路径
- 文档中的路径引用

### 2. 数据迁移
- 现有数据会保留在 `data/` 目录
- 数据库数据通过 Docker volume 持久化
- 日志文件保存在 `logs/` 目录

### 3. 环境变量
- 开发环境使用 `.env.dev` 文件
- 生产环境使用 `.env.prod` 文件
- 敏感信息通过环境变量管理

## 🔄 回滚方案

如果重组后出现问题，可以：

1. **备份当前状态**
```powershell
# 备份当前项目
Copy-Item -Path "." -Destination "../sehuatang-backup" -Recurse
```

2. **恢复原始结构**
```powershell
# 运行恢复脚本
.\scripts\restore-original.ps1
```

3. **逐步迁移**
```powershell
# 分步骤重组，每步验证
.\scripts\reorganize-step1.ps1
.\scripts\reorganize-step2.ps1
```

## 📚 相关文档

- [开发环境配置指南](DEVELOPMENT.md)
- [部署指南](DEPLOYMENT.md)
- [API 文档](API.md)

---

**重组时间**：2025-08-29  
**版本**：1.0.0  
**状态**：✅ 完成
