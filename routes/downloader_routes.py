#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载器推送API路由
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from db import get_db
from settings_manager import SettingsManager
from downloader_manager import DownloaderFactory, DownloaderManager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class MagnetPushRequest(BaseModel):
    """磁力链接推送请求模型"""
    magnet_url: str
    title: Optional[str] = ""
    tags: Optional[List[str]] = []

class BatchMagnetPushRequest(BaseModel):
    """批量磁力链接推送请求模型"""
    magnet_urls: List[str]
    title_prefix: Optional[str] = ""
    tags: Optional[List[str]] = []

@router.post("/api/downloader/push-magnet")
def push_magnet(request: MagnetPushRequest, db: Session = Depends(get_db)):
    """推送单个磁力链接到下载器"""
    try:
        # 创建下载器实例，传递数据库会话
        downloader = DownloaderManager(db)
        
        # 推送磁力链接
        result = downloader.push_magnet(
            magnet_url=request.magnet_url,
            title=request.title,
            tags=request.tags
        )
        
        return {
            "success": result["success"],
            "message": result["message"],
            "data": result.get("data", {})
        }
    except Exception as e:
        logger.error(f"推送磁力链接失败: {e}")
        raise HTTPException(status_code=500, detail=f"推送失败: {str(e)}")

@router.post("/api/downloader/push-batch")
def push_batch_magnets(request: BatchMagnetPushRequest, db: Session = Depends(get_db)):
    """批量推送磁力链接到下载器"""
    try:
        # 创建下载器实例，传递数据库会话
        downloader = DownloaderManager(db)
        
        results = []
        success_count = 0
        failed_count = 0
        
        for i, magnet_url in enumerate(request.magnet_urls):
            title = f"{request.title_prefix} {i+1}" if request.title_prefix else f"磁力链接 {i+1}"
            
            result = downloader.push_magnet(
                magnet_url=magnet_url,
                title=title,
                tags=request.tags
            )
            
            results.append({
                "index": i + 1,
                "magnet_url": magnet_url,
                "success": result["success"],
                "message": result["message"]
            })
            
            if result["success"]:
                success_count += 1
            else:
                failed_count += 1
        
        return {
            "success": True,
            "message": f"批量推送完成，成功: {success_count}，失败: {failed_count}",
            "data": {
                "total": len(request.magnet_urls),
                "success_count": success_count,
                "failed_count": failed_count,
                "results": results
            }
        }
    except Exception as e:
        logger.error(f"批量推送磁力链接失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量推送失败: {str(e)}")

@router.post("/api/downloader/push-from-database")
def push_magnets_from_database(
    magnet_ids: List[int], 
    db: Session = Depends(get_db)
):
    """从数据库推送指定的磁力链接到下载器"""
    try:
        from models_magnet import MagnetLink
        
        # 获取磁力链接数据
        magnets = db.query(MagnetLink).filter(MagnetLink.id.in_(magnet_ids)).all()
        
        if not magnets:
            return {
                "success": False,
                "message": "未找到指定的磁力链接",
                "data": {}
            }
        
        # 创建下载器实例，传递数据库会话
        downloader = DownloaderManager(db)
        
        results = []
        success_count = 0
        failed_count = 0
        
        for magnet in magnets:
            # 构建标签
            tags = []
            if magnet.forum_type:
                tags.append(magnet.forum_type)
            if magnet.author:
                tags.append(magnet.author)
            if magnet.is_uncensored:
                tags.append("无码")
            else:
                tags.append("有码")
            
            result = downloader.push_magnet(
                magnet_url=magnet.magnet_url,
                title=magnet.title or f"磁力链接 {magnet.id}",
                tags=tags
            )
            
            results.append({
                "id": magnet.id,
                "title": magnet.title,
                "magnet_url": magnet.magnet_url,
                "success": result["success"],
                "message": result["message"]
            })
            
            if result["success"]:
                success_count += 1
            else:
                failed_count += 1
        
        return {
            "success": True,
            "message": f"数据库推送完成，成功: {success_count}，失败: {failed_count}",
            "data": {
                "total": len(magnets),
                "success_count": success_count,
                "failed_count": failed_count,
                "results": results
            }
        }
    except Exception as e:
        logger.error(f"从数据库推送磁力链接失败: {e}")
        raise HTTPException(status_code=500, detail=f"数据库推送失败: {str(e)}")

@router.get("/api/downloader/status")
def get_downloader_status(db: Session = Depends(get_db)):
    """获取下载器状态"""
    try:
        # 添加调试信息
        logger.info("开始获取下载器状态")
        
        # 检查数据库会话
        logger.info(f"数据库会话状态: {db.is_active}")
        
        # 创建下载器实例，传递数据库会话
        downloader = DownloaderManager(db)
        
        # 获取下载器状态
        result = downloader.get_downloader_status()
        
        logger.info(f"下载器状态结果: {result}")
        
        return result
    except Exception as e:
        logger.error(f"获取下载器状态失败: {e}")
        return {
            "success": False,
            "message": f"获取状态失败: {str(e)}",
            "data": {}
        }
