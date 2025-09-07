# SEHUATANG 爬虫系统

一个专为影视爱好者设计的磁力链接爬取、管理和推送工具。支持可视化番号库管理，提供搜索筛选和批量磁力链接复制功能，支持推送磁力链接到 qBittorrent 等下载器，以及 115 网盘离线下载。

## 快速开始

### 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 1GB 内存
- 至少 10GB 可用磁盘空间

### 生产环境部署

1. **创建部署目录**
```bash
mkdir sehuatang-crawler
cd sehuatang-crawler
```

2. **创建 docker-compose.yml 文件**
```yaml
version: '3.8'

services:
  sehuatang-crawler:
    image: wyh3210277395/sehuatang-crawler:latest
    container_name: sehuatang-crawler
    ports:
      - "8000:8000"
    environment:
      # 数据库配置
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
      - DATABASE_NAME=sehuatang_db
      - DATABASE_USER=postgres
      - DATABASE_PASSWORD=postgres123
      
      # 应用配置
      - PYTHONPATH=/app/backend
      - ENVIRONMENT=production
      - ADMIN_PASSWORD=admin123
      
      # 代理配置（可选）
      - HTTP_PROXY=http://your-proxy:port
      - HTTPS_PROXY=http://your-proxy:port
      - NO_PROXY=localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12
      
      # Telegram 机器人配置（可选）
      - TELEGRAM_BOT_TOKEN=你的Bot_Token
      - TELEGRAM_BOT_WEBHOOK_URL=  # 可选，留空使用轮询模式
      - TELEGRAM_BOT_WEBHOOK_SECRET=  # 可选
      
      # CloudDrive2 配置（可选）
      - CLOUDDRIVE_HOST=你的CD2主机地址
      - CLOUDDRIVE_PORT=你的CD2端口
      
      # MetaTube 配置（可选）
      - METATUBE_URL=http://your-metatube-server:port
 

    volumes:
      - sehuatang_data:/app/data
      - sehuatang_logs:/app/logs
    
    depends_on:
      - postgres
    
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: sehuatang-postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=sehuatang_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres123
    
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
    restart: unless-stopped

volumes:
  sehuatang_data:
  sehuatang_logs:
  postgres_data:

networks:
  default:
    name: sehuatang-network
```

3. **启动服务**
```bash
docker-compose up -d
```

4. **访问系统**
- 访问地址：http://localhost:8000
- 默认密码：admin123

### 配置说明

主要配置项（在docker-compose.yml中修改）：
- `ADMIN_PASSWORD` - 管理员密码（默认：admin123）
- `DATABASE_PASSWORD` - 数据库密码（默认：postgres123）
- `HTTP_PROXY` - HTTP 代理（可选，如需要代理访问外网）
- `NO_PROXY` - 不走代理的地址（内网地址）

#### 下载器配置

在系统设置页面配置下载器连接信息：
- **qBittorrent**: 支持 Web UI 连接
- **CloudDrive2**: 支持 CD2 推送至115离线功能


#### 可选服务配置

- **Telegram Bot**: 配置 Bot Token 启用消息推送功能
- **MetaTube**: 配置 API 地址和密钥启用元数据增强功能
- **CloudDrive2**: 配置 CD2 服务器地址和端口

## 管理命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 更新到最新版本
docker-compose pull
docker-compose up -d
```

## 功能特性

- 🔍 **智能爬取**: 支持站点磁力链接爬取
- 📊 **可视化管理**: 直观的番号库管理界面
- 🔗 **批量操作**: 支持批量磁力链接复制和推送
- 📱 **移动端适配**: 响应式设计，支持手机访问
- 🤖 **Telegram 集成**: 支持 Telegram Bot
- ☁️ **云盘支持**: CloudDrive2 的 115 离线推送
- 🎬 **元数据增强**: 集成 MetaTube 获取详细信息

## 💰 赞赏支持

如果这个项目对你有帮助，欢迎赞赏支持～非常感谢！

<div align="center">
  <img src="https://youke1.picui.cn/s1/2025/09/07/68bd4edae214b.jpg" alt="微信赞赏码" width="360">
  
  <br/>
  <br/>
  

</div>

### 其他支持方式

- ⭐ **GitHub Star**: 给项目点个星星
- 🐛 **Bug 反馈**: 提交 Issue 帮助改进
- 💡 **功能建议**: 分享您的想法和需求
- 📢 **推荐分享**: 向朋友推荐这个项目

## 社区支持

- 💬 **交流群**: [Telegram 群组](https://t.me/sehuangtangcrawler)
- 🐳 **Docker 镜像**: [wyh3210277395/sehuatang-crawler](https://hub.docker.com/r/wyh3210277395/sehuatang-crawler)

## 许可证

MIT License

## 免责声明

本项目仅供学习和研究使用，请遵守相关法律法规，不得用于商业用途。使用者需自行承担使用风险。

---

<div align="center">

**感谢您的支持与关注！** 🙏

*如果您觉得这个项目有价值，请考虑赞赏支持开发者*

</div>