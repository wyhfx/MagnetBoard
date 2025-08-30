#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
磁力链接API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc, and_, or_
from typing import List, Optional
from db import get_db
from models_magnet import MagnetLink
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

# 论坛映射
FORUMS = {
    "36": "亚洲无码",
    "37": "亚洲有码", 
    "2": "国产原创",
    "103": "高清中文字幕",
    "104": "素人原创",
    "39": "动漫原创",
    "152": "韩国主播"
}

@router.get("/api/magnets")
def get_magnets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: Optional[str] = None,
    forum_type: Optional[str] = None,
    forum_id: Optional[str] = None,
    author: Optional[str] = None,
    is_uncensored: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取磁力链接列表"""
    try:
        query = db.query(MagnetLink)
        
        # 搜索过滤
        if q:
            search_filter = or_(
                MagnetLink.code.ilike(f"%{q}%"),
                MagnetLink.title.ilike(f"%{q}%"),
                MagnetLink.author.ilike(f"%{q}%"),
                MagnetLink.content.ilike(f"%{q}%")
            )
            query = query.filter(search_filter)
        
        # 论坛类型过滤
        if forum_type:
            query = query.filter(MagnetLink.forum_type == forum_type)
        
        # 论坛板块过滤
        if forum_id:
            query = query.filter(MagnetLink.forum_id == forum_id)
        
        # 作者过滤
        if author:
            query = query.filter(MagnetLink.author.ilike(f"%{author}%"))
        
        # 是否无码过滤
        if is_uncensored is not None:
            query = query.filter(MagnetLink.is_uncensored == is_uncensored)
        
        # 获取总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        magnets = query.order_by(desc(MagnetLink.created_at)).offset(offset).limit(page_size).all()
        
        # 转换为字典
        magnets_data = []
        for magnet in magnets:
            magnet_dict = {
                "id": magnet.id,
                "title": magnet.title,
                "content": magnet.content,
                "code": magnet.code,
                "author": magnet.author,
                "size": magnet.size,
                "is_uncensored": magnet.is_uncensored,
                "forum_id": magnet.forum_id,
                "forum_type": magnet.forum_type,
                "magnet_hash": magnet.magnet_hash,
                "created_at": magnet.created_at.isoformat() if magnet.created_at else None,
                "url": magnet.url,
                "magnets": json.loads(magnet.magnets) if magnet.magnets else [],
                "images": json.loads(magnet.images) if magnet.images else [],
                "cover_url": magnet.cover_url,
                "screenshot_urls": magnet.screenshot_urls,
                "poster_urls": magnet.poster_urls
            }
            magnets_data.append(magnet_dict)
        
        return {
            "success": True,
            "data": {
                "data": magnets_data,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        logger.error(f"获取磁力链接列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取磁力链接列表失败: {str(e)}")

@router.get("/api/magnets/{magnet_id}")
def get_magnet_by_id(magnet_id: int, db: Session = Depends(get_db)):
    """根据ID获取磁力链接详情"""
    try:
        magnet = db.query(MagnetLink).filter(MagnetLink.id == magnet_id).first()
        if not magnet:
            raise HTTPException(status_code=404, detail="磁力链接不存在")
        
        magnet_dict = {
            "id": magnet.id,
            "title": magnet.title,
            "content": magnet.content,
            "code": magnet.code,
            "author": magnet.author,
            "size": magnet.size,
            "is_uncensored": magnet.is_uncensored,
            "forum_id": magnet.forum_id,
            "forum_type": magnet.forum_type,
            "magnet_hash": magnet.magnet_hash,
            "created_at": magnet.created_at.isoformat() if magnet.created_at else None,
            "url": magnet.url,
            "magnets": json.loads(magnet.magnets) if magnet.magnets else [],
            "images": json.loads(magnet.images) if magnet.images else [],
            "cover_url": magnet.cover_url,
            "screenshot_urls": magnet.screenshot_urls,
            "poster_urls": magnet.poster_urls
        }
        
        return {"success": True, "data": magnet_dict}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取磁力链接详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取磁力链接详情失败: {str(e)}")

@router.get("/api/magnets/code/{code}")
def get_magnet_by_code(code: str, db: Session = Depends(get_db)):
    """根据番号获取磁力链接"""
    try:
        magnet = db.query(MagnetLink).filter(MagnetLink.code == code).first()
        if not magnet:
            raise HTTPException(status_code=404, detail="磁力链接不存在")
        
        magnet_dict = {
            "id": magnet.id,
            "title": magnet.title,
            "content": magnet.content,
            "code": magnet.code,
            "author": magnet.author,
            "size": magnet.size,
            "is_uncensored": magnet.is_uncensored,
            "forum_id": magnet.forum_id,
            "forum_type": magnet.forum_type,
            "magnet_hash": magnet.magnet_hash,
            "created_at": magnet.created_at.isoformat() if magnet.created_at else None,
            "url": magnet.url,
            "magnets": json.loads(magnet.magnets) if magnet.magnets else [],
            "images": json.loads(magnet.images) if magnet.images else [],
            "cover_url": magnet.cover_url,
            "screenshot_urls": magnet.screenshot_urls,
            "poster_urls": magnet.poster_urls
        }
        
        return {"success": True, "data": magnet_dict}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"根据番号获取磁力链接失败: {e}")
        raise HTTPException(status_code=500, detail=f"根据番号获取磁力链接失败: {str(e)}")

@router.get("/api/magnets/stats")
def get_magnet_stats(db: Session = Depends(get_db)):
    """获取磁力链接统计信息"""
    try:
        # 总数
        total_count = db.query(MagnetLink).count()
        
        # 今日新增
        today_count = db.query(MagnetLink).filter(
            func.date(MagnetLink.created_at) == func.current_date()
        ).count()
        
        # 论坛分布
        forum_stats = db.query(
            MagnetLink.forum_id,
            func.count(MagnetLink.id).label('count')
        ).group_by(MagnetLink.forum_id).all()
        
        forum_distribution = {}
        for forum_id, count in forum_stats:
            forum_name = FORUMS.get(forum_id, f"未知论坛({forum_id})")
            forum_distribution[forum_name] = count
        
        # 作者分布
        author_stats = db.query(
            MagnetLink.author,
            func.count(MagnetLink.id).label('count')
        ).filter(MagnetLink.author.isnot(None)).group_by(MagnetLink.author).order_by(
            desc(func.count(MagnetLink.id))
        ).limit(10).all()
        
        return {
            "success": True,
            "data": {
                "total_count": total_count,
                "today_count": today_count,
                "forum_distribution": forum_distribution,
                "top_authors": [{"author": author, "count": count} for author, count in author_stats]
            }
        }
        
    except Exception as e:
        logger.error(f"获取磁力链接统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取磁力链接统计失败: {str(e)}")

@router.get("/api/forums")
def get_forums():
    """获取所有论坛板块"""
    try:
        forums = []
        for forum_id, forum_name in FORUMS.items():
            forums.append({
                "id": forum_id,
                "name": forum_name,
                "type": "standard_av" if forum_id in ["36", "37", "2", "103", "104"] else "non_av"
            })
        return {"success": True, "data": forums}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取论坛列表失败: {str(e)}")

# 批量操作API
@router.post("/api/magnets/batch-delete")
def batch_delete_magnets(ids: List[int], db: Session = Depends(get_db)):
    """批量删除磁力链接"""
    try:
        if not ids:
            raise HTTPException(status_code=400, detail="请选择要删除的项目")
        
        # 删除选中的磁力链接
        deleted_count = db.query(MagnetLink).filter(MagnetLink.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        
        logger.info(f"批量删除了 {deleted_count} 个磁力链接")
        
        return {
            "success": True,
            "message": f"成功删除 {deleted_count} 个项目",
            "data": {"deleted_count": deleted_count}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"批量删除磁力链接失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量删除失败: {str(e)}")

@router.post("/api/magnets/batch-export")
def batch_export_magnets(ids: List[int], export_type: str = "magnets", db: Session = Depends(get_db)):
    """批量导出磁力链接"""
    try:
        if not ids:
            raise HTTPException(status_code=400, detail="请选择要导出的项目")
        
        # 获取选中的磁力链接
        magnets = db.query(MagnetLink).filter(MagnetLink.id.in_(ids)).all()
        
        if export_type == "magnets":
            # 导出磁力链接
            magnet_links = []
            for magnet in magnets:
                if magnet.magnets:
                    magnet_links.extend(json.loads(magnet.magnets))
            
            return {
                "success": True,
                "data": {
                    "type": "magnets",
                    "content": "\n".join(magnet_links),
                    "count": len(magnet_links)
                }
            }
        elif export_type == "details":
            # 导出详细信息
            details = []
            for magnet in magnets:
                detail = {
                    "code": magnet.code,
                    "title": magnet.title,
                    "author": magnet.author,
                    "size": magnet.size,
                    "forum": FORUMS.get(magnet.forum_id, f"未知论坛({magnet.forum_id})"),
                    "magnets": json.loads(magnet.magnets) if magnet.magnets else []
                }
                details.append(detail)
            
            return {
                "success": True,
                "data": {
                    "type": "details",
                    "content": details,
                    "count": len(details)
                }
            }
        else:
            raise HTTPException(status_code=400, detail="不支持的导出类型")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量导出磁力链接失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量导出失败: {str(e)}")

@router.post("/api/magnets/batch-mark")
def batch_mark_magnets(ids: List[int], action: str, db: Session = Depends(get_db)):
    """批量标记磁力链接"""
    try:
        if not ids:
            raise HTTPException(status_code=400, detail="请选择要标记的项目")
        
        if action not in ["favorite", "unfavorite", "read", "unread"]:
            raise HTTPException(status_code=400, detail="不支持的标记操作")
        
        # 这里可以添加标记字段到数据库模型中
        # 暂时返回成功消息
        return {
            "success": True,
            "message": f"成功标记 {len(ids)} 个项目",
            "data": {"marked_count": len(ids)}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量标记磁力链接失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量标记失败: {str(e)}")
