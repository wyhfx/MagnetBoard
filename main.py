#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sehuatang 爬虫系统主应用
集成所有功能模块和API路由
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# 导入数据库和模型
from db import engine, Base
from models_magnet import MagnetLink
from models_settings import Setting
from models_scheduler import ScheduledTask
from models_logs import LogEntry  # 添加日志模型导入

# 导入路由
from routes.magnet_routes import router as magnet_router
from routes.settings_routes import router as settings_router
from routes.proxy_routes import router as proxy_router
from routes.dashboard_routes import router as dashboard_router
from routes.search_routes import router as search_router
# from routes.metadata_refresh import router as metadata_router
from routes.crawler_routes import router as crawler_router
from routes.jobs_routes import router as jobs_router
from routes.logs_routes import router as logs_router
from routes.delete_routes import router as delete_router
from routes.scheduler_routes import router as scheduler_router
from routes.downloader_routes import router as downloader_router

# 导入设置管理器
from settings_manager import SettingsManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("🚀 启动 Sehuatang 爬虫系统...")
    
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")
    
    # 初始化设置
    try:
        from migrate_settings_table import create_settings_table
        create_settings_table()
        print("✅ 设置表初始化完成")
    except Exception as e:
        print(f"⚠️ 设置表初始化失败: {e}")
    
    # 初始化磁力链接表
    try:
        # 直接创建表，不需要额外的迁移脚本
        Base.metadata.create_all(bind=engine)
        print("✅ 磁力链接表初始化完成")
    except Exception as e:
        print(f"⚠️ 磁力链接表初始化失败: {e}")
    
    yield
    
    # 关闭时执行
    print("🛑 关闭 Sehuatang 爬虫系统...")

# 创建FastAPI应用
app = FastAPI(
    title="Sehuatang 爬虫系统",
    description="一个强大的磁力链接管理和元数据获取工具",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(magnet_router, tags=["磁力链接"])
app.include_router(settings_router, tags=["系统设置"])
app.include_router(proxy_router, tags=["代理管理"])
app.include_router(dashboard_router, tags=["仪表盘"])
app.include_router(search_router, tags=["搜索"])
# app.include_router(metadata_router, tags=["元数据"]) # 注释掉metadata_refresh路由
app.include_router(crawler_router, tags=["爬虫管理"])
app.include_router(jobs_router, tags=["任务调度"])
app.include_router(logs_router, tags=["系统日志"])
app.include_router(delete_router, tags=["删除管理"])
app.include_router(scheduler_router, tags=["定时任务"])
app.include_router(downloader_router, tags=["下载器"])

# 静态文件服务
if os.path.exists("frontend/build"):
    # 挂载静态文件目录
    app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")
    
    # 提供前端文件
    from fastapi.responses import FileResponse, HTMLResponse
    from fastapi.responses import RedirectResponse
    import mimetypes
    
    @app.get("/", include_in_schema=False)
    def serve_frontend():
        """提供前端首页"""
        return FileResponse("frontend/build/index.html")
    
    @app.get("/manifest.json", include_in_schema=False)
    def serve_manifest():
        """提供 manifest.json 文件"""
        return FileResponse("frontend/build/manifest.json")
    
    @app.get("/favicon.ico", include_in_schema=False)
    def serve_favicon():
        """提供 favicon.ico 文件"""
        return FileResponse("frontend/build/favicon.ico")
    
    @app.get("/logo192.png", include_in_schema=False)
    def serve_logo192():
        """提供 logo192.png 文件"""
        return FileResponse("frontend/build/logo192.png")
    
    @app.get("/logo512.png", include_in_schema=False)
    def serve_logo512():
        """提供 logo512.png 文件"""
        return FileResponse("frontend/build/logo512.png")
    
    @app.get("/robots.txt", include_in_schema=False)
    def serve_robots():
        """提供 robots.txt 文件"""
        return FileResponse("frontend/build/robots.txt")
    
    # 健康检查 - 必须在通用路由之前定义
    @app.get("/health")
    def health_check():
        """健康检查接口"""
        return {
            "status": "healthy",
            "message": "Sehuatang 爬虫系统运行正常",
            "version": "1.0.0"
        }
    
    # 处理前端路由（SPA路由）
    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa_routes(full_path: str):
        """处理前端SPA路由，所有未匹配的路径都返回index.html"""
        # 如果是API路径，返回404
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        # 如果是静态资源，返回404（让上面的静态文件处理器处理）
        if full_path.startswith("static/"):
            raise HTTPException(status_code=404, detail="Static file not found")
        
        # 其他路径都返回index.html（SPA路由）
        return FileResponse("frontend/build/index.html")
else:
    # 如果没有前端文件，提供API信息
    @app.get("/", include_in_schema=False)
    def root():
        """根路径健康检查"""
        return {
            "message": "Sehuatang 爬虫系统 API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs"
        }



# 系统信息
@app.get("/api/system/info")
def get_system_info():
    """获取系统信息"""
    try:
        from db import SessionLocal
        db = SessionLocal()
        
        # 获取统计信息
        magnet_count = db.query(MagnetLink).count()
        settings_count = db.query(Setting).count()
        
        db.close()
        
        return {
            "success": True,
            "data": {
                "magnet_count": magnet_count,
                "settings_count": settings_count,
                "version": "1.0.0"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}")



if __name__ == "__main__":
    # 获取配置（支持Docker环境变量）
    host = os.getenv("APP_HOST", os.getenv("HOST", "0.0.0.0"))
    port = int(os.getenv("APP_PORT", os.getenv("PORT", "8000")))
    reload = os.getenv("APP_RELOAD", os.getenv("DEBUG", "false")).lower() == "true"
    
    print(f"🌐 启动服务器: http://{host}:{port}")
    print(f"📚 API文档: http://{host}:{port}/docs")
    print(f"🔧 重载模式: {reload}")
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
