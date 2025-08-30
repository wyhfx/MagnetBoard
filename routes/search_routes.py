#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, distinct
from db import get_db
from models_magnet import MagnetLink
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/search/suggestions")
def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=50),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """获取搜索建议"""
    try:
        if not q or len(q.strip()) < 1:
            return {"success": True, "data": []}
        
        query = q.strip()
        
        # 1. 番号建议
        code_suggestions = db.query(
            MagnetLink.code,
            func.count(MagnetLink.id).label('count')
        ).filter(
            MagnetLink.code.ilike(f"%{query}%"),
            MagnetLink.code.isnot(None),
            MagnetLink.code != ""
        ).group_by(MagnetLink.code).order_by(
            desc(func.count(MagnetLink.id))
        ).limit(limit // 2).all()
        
        # 2. 作者建议
        author_suggestions = db.query(
            MagnetLink.author,
            func.count(MagnetLink.id).label('count')
        ).filter(
            MagnetLink.author.ilike(f"%{query}%"),
            MagnetLink.author.isnot(None),
            MagnetLink.author != ""
        ).group_by(MagnetLink.author).order_by(
            desc(func.count(MagnetLink.id))
        ).limit(limit // 2).all()
        
        # 3. 标题关键词建议
        title_suggestions = db.query(
            MagnetLink.title,
            func.count(MagnetLink.id).label('count')
        ).filter(
            MagnetLink.title.ilike(f"%{query}%"),
            MagnetLink.title.isnot(None),
            MagnetLink.title != ""
        ).group_by(MagnetLink.title).order_by(
            desc(func.count(MagnetLink.id))
        ).limit(limit // 2).all()
        
        # 合并建议
        suggestions = []
        
        # 添加番号建议
        for code, count in code_suggestions:
            suggestions.append({
                "type": "code",
                "value": code,
                "count": count,
                "display": f"番号: {code} ({count}个)"
            })
        
        # 添加作者建议
        for author, count in author_suggestions:
            suggestions.append({
                "type": "author",
                "value": author,
                "count": count,
                "display": f"作者: {author} ({count}个)"
            })
        
        # 添加标题建议
        for title, count in title_suggestions:
            # 截取标题前50个字符
            short_title = title[:50] + "..." if len(title) > 50 else title
            suggestions.append({
                "type": "title",
                "value": title,
                "count": count,
                "display": f"标题: {short_title} ({count}个)"
            })
        
        # 按数量排序并去重
        seen_values = set()
        unique_suggestions = []
        for suggestion in sorted(suggestions, key=lambda x: x['count'], reverse=True):
            if suggestion['value'] not in seen_values:
                seen_values.add(suggestion['value'])
                unique_suggestions.append(suggestion)
                if len(unique_suggestions) >= limit:
                    break
        
        return {
            "success": True,
            "data": unique_suggestions
        }
        
    except Exception as e:
        logger.error(f"获取搜索建议失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取搜索建议失败: {str(e)}")

@router.get("/api/search/popular")
def get_popular_searches(db: Session = Depends(get_db)):
    """获取热门搜索"""
    try:
        # 获取热门番号
        popular_codes = db.query(
            MagnetLink.code,
            func.count(MagnetLink.id).label('count')
        ).filter(
            MagnetLink.code.isnot(None),
            MagnetLink.code != ""
        ).group_by(MagnetLink.code).order_by(
            desc(func.count(MagnetLink.id))
        ).limit(10).all()
        
        # 获取热门作者
        popular_authors = db.query(
            MagnetLink.author,
            func.count(MagnetLink.id).label('count')
        ).filter(
            MagnetLink.author.isnot(None),
            MagnetLink.author != ""
        ).group_by(MagnetLink.author).order_by(
            desc(func.count(MagnetLink.id))
        ).limit(10).all()
        
        # 获取热门论坛
        popular_forums = db.query(
            MagnetLink.forum_id,
            func.count(MagnetLink.id).label('count')
        ).group_by(MagnetLink.forum_id).order_by(
            desc(func.count(MagnetLink.id))
        ).limit(5).all()
        
        return {
            "success": True,
            "data": {
                "popular_codes": [{"code": code, "count": count} for code, count in popular_codes],
                "popular_authors": [{"author": author, "count": count} for author, count in popular_authors],
                "popular_forums": [{"forum_id": forum_id, "count": count} for forum_id, count in popular_forums]
            }
        }
        
    except Exception as e:
        logger.error(f"获取热门搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取热门搜索失败: {str(e)}")

@router.get("/api/search/recent")
def get_recent_searches(db: Session = Depends(get_db)):
    """获取最近搜索（基于最近添加的数据）"""
    try:
        # 获取最近添加的番号
        recent_codes = db.query(
            MagnetLink.code,
            MagnetLink.created_at
        ).filter(
            MagnetLink.code.isnot(None),
            MagnetLink.code != ""
        ).order_by(
            desc(MagnetLink.created_at)
        ).limit(10).all()
        
        # 获取最近添加的作者
        recent_authors = db.query(
            MagnetLink.author,
            MagnetLink.created_at
        ).filter(
            MagnetLink.author.isnot(None),
            MagnetLink.author != ""
        ).order_by(
            desc(MagnetLink.created_at)
        ).limit(10).all()
        
        return {
            "success": True,
            "data": {
                "recent_codes": [{"code": code, "date": created_at.isoformat()} for code, created_at in recent_codes],
                "recent_authors": [{"author": author, "date": created_at.isoformat()} for author, created_at in recent_authors]
            }
        }
        
    except Exception as e:
        logger.error(f"获取最近搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取最近搜索失败: {str(e)}")

@router.get("/api/search/trending")
def get_trending_searches(db: Session = Depends(get_db)):
    """获取趋势搜索（最近7天热门）"""
    try:
        from datetime import datetime, timedelta
        
        # 最近7天
        week_ago = datetime.now() - timedelta(days=7)
        
        # 最近7天热门番号
        trending_codes = db.query(
            MagnetLink.code,
            func.count(MagnetLink.id).label('count')
        ).filter(
            MagnetLink.code.isnot(None),
            MagnetLink.code != "",
            MagnetLink.created_at >= week_ago
        ).group_by(MagnetLink.code).order_by(
            desc(func.count(MagnetLink.id))
        ).limit(10).all()
        
        # 最近7天热门作者
        trending_authors = db.query(
            MagnetLink.author,
            func.count(MagnetLink.id).label('count')
        ).filter(
            MagnetLink.author.isnot(None),
            MagnetLink.author != "",
            MagnetLink.created_at >= week_ago
        ).group_by(MagnetLink.author).order_by(
            desc(func.count(MagnetLink.id))
        ).limit(10).all()
        
        return {
            "success": True,
            "data": {
                "trending_codes": [{"code": code, "count": count} for code, count in trending_codes],
                "trending_authors": [{"author": author, "count": count} for author, count in trending_authors]
            }
        }
        
    except Exception as e:
        logger.error(f"获取趋势搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取趋势搜索失败: {str(e)}")
