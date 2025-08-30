# routes/crawler_routes.py
import json
import logging
import hashlib
import re
import asyncio
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db import get_db, SessionLocal
from new_crawler_manager import get_crawler_manager
from settings_manager import get_settings_manager
from models_magnet import MagnetLink
from routes.logs_routes import emit_log

router = APIRouter(prefix="/api/crawler")
logger = logging.getLogger(__name__)

# 全局变量存储爬虫状态
crawler_status = {
    "is_running": False,
    "current_forum": None,
    "current_page": 0,
    "total_pages": 0,
    "crawled_count": 0,
    "error_count": 0
}

class CrawlRequest(BaseModel):
    forum_id: str = "36"  # 单个论坛ID
    start_page: int = 1
    end_page: int = 1
    save_to_db: bool = True
    proxy: Optional[str] = None
    keywords: Optional[List[str]] = None  # 关键词过滤
    delay_between_pages: int = 2  # 页面间延迟
    max_concurrent: int = 5  # 最大并发数

class CrawlResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None

class CrawlerStatusResponse(BaseModel):
    is_running: bool
    current_forum: Optional[str]
    current_page: int
    total_pages: int
    crawled_count: int
    error_count: int
    max_concurrent: Optional[int] = None
    proxy: Optional[str] = None
    cookies_file: Optional[str] = None

def progress_callback(progress: float, message: str):
    """进度回调函数"""
    global crawler_status
    crawler_status["current_page"] = int(progress)
    emit_log("INFO", f"爬虫进度: {progress:.1f}% - {message}")

def log_callback(timestamp: str, level: str, message: str):
    """日志回调函数"""
    emit_log(level, message)

def status_callback(status: str, data: Dict):
    """状态回调函数"""
    global crawler_status
    if status == "crawling":
        crawler_status["is_running"] = True
    elif status in ["completed", "error", "stopped"]:
        crawler_status["is_running"] = False
    
    emit_log("INFO", f"爬虫状态: {status} - {data.get('message', '')}")

@router.post("/start", response_model=CrawlResponse)
async def start_crawler(request: CrawlRequest, background_tasks: BackgroundTasks):
    """启动新爬虫系统"""
    try:
        # 获取爬虫管理器
        manager = get_crawler_manager()
        
        # 设置回调函数
        manager.set_progress_callback(progress_callback)
        manager.set_log_callback(log_callback)
        manager.set_status_callback(status_callback)
        
        # 检查是否已在运行
        if manager.is_running:
            raise HTTPException(status_code=400, detail="爬虫正在运行中")
        
        # 设置最大并发数
        manager.max_concurrent = request.max_concurrent
        
        # 启动爬虫任务
        background_tasks.add_task(
            manager.start_crawler,
            fid=request.forum_id,
            start_page=request.start_page,
            end_page=request.end_page,
            keywords=request.keywords,
            delay_between_pages=request.delay_between_pages
        )
        
        return CrawlResponse(
            success=True,
            message="爬虫启动成功",
            data={"forum_id": request.forum_id}
        )
        
    except Exception as e:
        logger.error(f"启动爬虫失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动爬虫失败: {str(e)}")

@router.post("/stop", response_model=CrawlResponse)
async def stop_crawler():
    """停止爬虫"""
    try:
        manager = get_crawler_manager()
        manager.stop_crawler()
        
        return CrawlResponse(
            success=True,
            message="爬虫停止命令已发送"
        )
        
    except Exception as e:
        logger.error(f"停止爬虫失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止爬虫失败: {str(e)}")

@router.get("/status")
async def get_crawler_status():
    """获取爬虫状态"""
    try:
        manager = get_crawler_manager()
        status = await manager.get_crawler_status()
        
        status_data = {
            "is_running": crawler_status["is_running"],
            "current_forum": crawler_status["current_forum"],
            "current_page": crawler_status["current_page"],
            "total_pages": crawler_status["total_pages"],
            "crawled_count": crawler_status["crawled_count"],
            "error_count": crawler_status["error_count"],
            "max_concurrent": manager.max_concurrent,
            "proxy": manager.proxy,
            "cookies_file": manager.cookies_file
        }
        
        return {
            "success": True,
            "data": status_data
        }
        
    except Exception as e:
        logger.error(f"获取爬虫状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取爬虫状态失败: {str(e)}")

@router.get("/themes")
async def get_available_themes():
    """获取可用主题列表"""
    try:
        manager = get_crawler_manager()
        themes = manager.get_available_themes()
        
        return {
            "success": True,
            "data": themes
        }
        
    except Exception as e:
        logger.error(f"获取主题列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取主题列表失败: {str(e)}")

@router.post("/collect-cookies", response_model=CrawlResponse)
async def collect_cookies_manual():
    """手动收集cookies"""
    try:
        manager = get_crawler_manager()
        manager.set_log_callback(log_callback)
        manager.set_status_callback(status_callback)
        
        success = await manager.manual_refresh_cookies()
        
        if success:
            return CrawlResponse(
                success=True,
                message="cookies收集成功"
            )
        else:
            return CrawlResponse(
                success=False,
                message="cookies收集失败"
            )
        
    except Exception as e:
        logger.error(f"收集cookies失败: {e}")
        raise HTTPException(status_code=500, detail=f"收集cookies失败: {str(e)}")

@router.post("/test-connection", response_model=CrawlResponse)
async def test_connection():
    """测试连接"""
    try:
        manager = get_crawler_manager()
        manager.set_log_callback(log_callback)
        
        success = await manager.test_connection_with_retry()
        
        if success:
            return CrawlResponse(
                success=True,
                message="连接测试成功"
            )
        else:
            return CrawlResponse(
                success=False,
                message="连接测试失败"
            )
        
    except Exception as e:
        logger.error(f"连接测试失败: {e}")
        raise HTTPException(status_code=500, detail=f"连接测试失败: {str(e)}")

@router.post("/set-max-concurrent")
async def set_max_concurrent(request: dict):
    """设置最大并发数"""
    try:
        max_concurrent = request.get("max_concurrent")
        if not max_concurrent:
            raise HTTPException(status_code=400, detail="缺少max_concurrent参数")
        
        max_concurrent = int(max_concurrent)
        if max_concurrent < 1 or max_concurrent > 20:
            raise HTTPException(status_code=400, detail="最大并发数必须在1-20之间")
        
        manager = get_crawler_manager()
        manager.max_concurrent = max_concurrent
        
        return {"success": True, "message": f"最大并发数已设置为 {max_concurrent}"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="max_concurrent必须是有效的数字")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置最大并发数失败: {e}")
        raise HTTPException(status_code=500, detail=f"设置最大并发数失败: {str(e)}")
