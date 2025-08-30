#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪表板API路由
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, extract
from db import get_db
from models_magnet import MagnetLink
from models_logs import LogEntry
import logging
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List
import math

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取仪表板统计数据"""
    try:
        # 基础统计
        total_magnets = db.query(MagnetLink).count()
        
        # 今日新增
        today = datetime.now().date()
        today_magnets = db.query(MagnetLink).filter(
            func.date(MagnetLink.created_at) == today
        ).count()
        
        # 本周新增
        week_ago = today - timedelta(days=7)
        week_magnets = db.query(MagnetLink).filter(
            MagnetLink.created_at >= week_ago
        ).count()
        
        # 本月新增
        month_ago = today - timedelta(days=30)
        month_magnets = db.query(MagnetLink).filter(
            MagnetLink.created_at >= month_ago
        ).count()
        
        # 论坛分布
        forum_stats = db.query(
            MagnetLink.forum_id,
            func.count(MagnetLink.id).label('count')
        ).group_by(MagnetLink.forum_id).all()
        
        forum_distribution = []
        for forum_id, count in forum_stats:
            forum_name = get_forum_name(forum_id)
            forum_distribution.append({
                "forum_id": forum_id,
                "forum_name": forum_name,
                "count": count,
                "percentage": round(count / total_magnets * 100, 2) if total_magnets > 0 else 0
            })
        
        # 按类型分布
        type_stats = db.query(
            MagnetLink.forum_type,
            func.count(MagnetLink.id).label('count')
        ).group_by(MagnetLink.forum_type).all()
        
        type_distribution = []
        for forum_type, count in type_stats:
            type_distribution.append({
                "type": forum_type,
                "count": count,
                "percentage": round(count / total_magnets * 100, 2) if total_magnets > 0 else 0
            })
        
        # 有码/无码分布
        censored_stats = db.query(
            MagnetLink.is_uncensored,
            func.count(MagnetLink.id).label('count')
        ).group_by(MagnetLink.is_uncensored).all()
        
        censored_distribution = []
        for is_uncensored, count in censored_stats:
            censored_distribution.append({
                "type": "无码" if is_uncensored else "有码",
                "count": count,
                "percentage": round(count / total_magnets * 100, 2) if total_magnets > 0 else 0
            })
        
        # 热门作者
        top_authors = db.query(
            MagnetLink.author,
            func.count(MagnetLink.id).label('count')
        ).filter(
            MagnetLink.author.isnot(None),
            MagnetLink.author != ""
        ).group_by(MagnetLink.author).order_by(
            desc(func.count(MagnetLink.id))
        ).limit(10).all()
        
        authors_data = []
        for author, count in top_authors:
            authors_data.append({
                "author": author,
                "count": count
            })
        
        # 每日新增趋势（最近30天）
        daily_stats = db.query(
            func.date(MagnetLink.created_at).label('date'),
            func.count(MagnetLink.id).label('count')
        ).filter(
            MagnetLink.created_at >= month_ago
        ).group_by(
            func.date(MagnetLink.created_at)
        ).order_by(
            func.date(MagnetLink.created_at)
        ).all()
        
        daily_trend = []
        for date, count in daily_stats:
            daily_trend.append({
                "date": date.strftime("%Y-%m-%d"),
                "count": count
            })
        
        # 文件大小分布
        size_stats = db.query(
            MagnetLink.size,
            func.count(MagnetLink.id).label('count')
        ).filter(
            MagnetLink.size.isnot(None),
            MagnetLink.size != ""
        ).group_by(MagnetLink.size).order_by(
            desc(func.count(MagnetLink.id))
        ).limit(10).all()
        
        size_distribution = []
        for size, count in size_stats:
            size_distribution.append({
                "size": size,
                "count": count
            })
        
        return {
            "success": True,
            "data": {
                "overview": {
                    "total_magnets": total_magnets,
                    "today_magnets": today_magnets,
                    "week_magnets": week_magnets,
                    "month_magnets": month_magnets
                },
                "forum_distribution": forum_distribution,
                "type_distribution": type_distribution,
                "censored_distribution": censored_distribution,
                "top_authors": authors_data,
                "daily_trend": daily_trend,
                "size_distribution": size_distribution
            }
        }
        
    except Exception as e:
        logger.error(f"获取仪表板统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

@router.get("/api/dashboard/system")
def get_system_stats():
    """获取系统监控数据"""
    try:
        # CPU使用率 - 修复Windows兼容性问题
        try:
            cpu_percent = psutil.cpu_percent()
        except Exception as e:
            logger.warning(f"获取CPU信息失败: {e}")
            cpu_percent = 0
        
        # 内存使用率
        memory = psutil.virtual_memory()
        memory_stats = {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent
        }
        
        # 磁盘使用率 - 修复Windows路径问题
        try:
            # 在Windows上使用当前工作目录的根目录
            if os.name == 'nt':  # Windows
                disk_path = os.path.splitdrive(os.getcwd())[0] + '\\'
            else:  # Unix/Linux
                disk_path = '/'
            
            disk = psutil.disk_usage(disk_path)
            disk_stats = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        except Exception as e:
            logger.warning(f"获取磁盘信息失败: {e}")
            disk_stats = {
                "total": 0,
                "used": 0,
                "free": 0,
                "percent": 0
            }
        
        # 网络统计
        try:
            network = psutil.net_io_counters()
            network_stats = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        except Exception as e:
            logger.warning(f"获取网络信息失败: {e}")
            network_stats = {
                "bytes_sent": 0,
                "bytes_recv": 0,
                "packets_sent": 0,
                "packets_recv": 0
            }
        
        return {
            "success": True,
            "data": {
                "cpu": {
                    "percent": cpu_percent
                },
                "memory": memory_stats,
                "disk": disk_stats,
                "network": network_stats,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"获取系统统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统统计失败: {str(e)}")

@router.get("/api/dashboard/performance")
def get_performance_stats(db: Session = Depends(get_db)):
    """获取性能统计"""
    try:
        # 最近24小时的错误日志统计
        yesterday = datetime.now() - timedelta(days=1)
        
        error_logs = db.query(LogEntry).filter(
            LogEntry.level == "ERROR",
            LogEntry.timestamp >= yesterday
        ).count()
        
        warning_logs = db.query(LogEntry).filter(
            LogEntry.level == "WARNING",
            LogEntry.timestamp >= yesterday
        ).count()
        
        info_logs = db.query(LogEntry).filter(
            LogEntry.level == "INFO",
            LogEntry.timestamp >= yesterday
        ).count()
        
        # 按小时统计错误
        hourly_errors = db.query(
            extract('hour', LogEntry.timestamp).label('hour'),
            func.count(LogEntry.id).label('count')
        ).filter(
            LogEntry.level == "ERROR",
            LogEntry.timestamp >= yesterday
        ).group_by(
            extract('hour', LogEntry.timestamp)
        ).order_by(
            extract('hour', LogEntry.timestamp)
        ).all()
        
        hourly_error_data = []
        for hour, count in hourly_errors:
            hourly_error_data.append({
                "hour": hour,
                "count": count
            })
        
        return {
            "success": True,
            "data": {
                "logs": {
                    "error_count": error_logs,
                    "warning_count": warning_logs,
                    "info_count": info_logs
                },
                "hourly_errors": hourly_error_data
            }
        }
        
    except Exception as e:
        logger.error(f"获取性能统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取性能统计失败: {str(e)}")

@router.get("/api/dashboard/storage-info")
def get_storage_info():
    """获取存储信息（数据库大小 + 图片大小）"""
    try:
        import os
        from pathlib import Path
        
        # 格式化大小函数
        def format_bytes(bytes_size):
            if bytes_size == 0:
                return "0 B"
            k = 1024
            sizes = ['B', 'KB', 'MB', 'GB', 'TB']
            i = int(math.floor(math.log(bytes_size) / math.log(k)))
            return f"{bytes_size / math.pow(k, i):.2f} {sizes[i]}"
        
        # 获取目录大小
        def get_directory_size(directory_path):
            total_size = 0
            file_count = 0
            try:
                if os.path.exists(directory_path):
                    for dirpath, dirnames, filenames in os.walk(directory_path):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            try:
                                total_size += os.path.getsize(filepath)
                                file_count += 1
                            except (OSError, IOError):
                                continue
            except Exception as e:
                logger.warning(f"获取目录 {directory_path} 大小失败: {e}")
            return total_size, file_count
        
        # 1. 数据库信息
        db_path = Path("data/app.db")
        db_size_bytes = 0
        table_count = 0
        table_sizes = []
        
        # 获取表信息
        try:
            from db import get_db
            from sqlalchemy import text
            
            db = next(get_db())
            
            # 获取表数量
            result = db.execute(text("""
                SELECT COUNT(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = result.scalar()
            
            # 获取各表大小
            result = db.execute(text("""
                SELECT 
                    table_name,
                    pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size,
                    pg_total_relation_size(quote_ident(table_name)) as size_bytes,
                    (SELECT reltuples FROM pg_class WHERE relname = table_name) as row_count
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC
            """))
            
            for row in result:
                table_sizes.append({
                    "table_name": row.table_name,
                    "size": row.size,
                    "size_bytes": row.size_bytes,
                    "row_count": int(row.row_count) if row.row_count else 0
                })
            
            # 计算数据库总大小（所有表的大小总和）
            db_size_bytes = sum(table["size_bytes"] for table in table_sizes)
            
            db.close()
            
        except Exception as e:
            logger.warning(f"获取表信息失败: {e}")
            # 如果PostgreSQL查询失败，回退到SQLite文件大小
            if db_path.exists():
                db_size_bytes = db_path.stat().st_size
        
        # 2. 图片信息 - 从数据库中统计图片URL数量
        try:
            from db import get_db
            from models_magnet import MagnetLink
            import json
            
            db = next(get_db())
            
            # 统计所有图片URL
            all_magnets = db.query(MagnetLink.images).all()
            total_image_urls = 0
            unique_image_urls = set()
            
            for magnet in all_magnets:
                if magnet.images:
                    try:
                        image_list = json.loads(magnet.images) if isinstance(magnet.images, str) else magnet.images
                        if isinstance(image_list, list):
                            total_image_urls += len(image_list)
                            unique_image_urls.update(image_list)
                    except (json.JSONDecodeError, TypeError):
                        continue
            
            images_count = len(unique_image_urls)
            # 计算图片链接的实际大小（字符数）
            total_image_chars = sum(len(str(magnet.images)) for magnet in all_magnets if magnet.images)
            estimated_image_size = total_image_chars  # 每个字符1字节
            
            db.close()
            
        except Exception as e:
            logger.warning(f"获取图片统计信息失败: {e}")
            images_count = 0
            estimated_image_size = 0
        
        # 3. 爬取结果文件信息
        crawler_results_path = Path("data/crawler_results")
        crawler_results_size_bytes, crawler_results_count = get_directory_size(crawler_results_path)
        
        # 4. 总存储信息
        total_size_bytes = db_size_bytes + estimated_image_size + crawler_results_size_bytes
        
        return {
            "success": True,
            "data": {
                "total": {
                    "size": format_bytes(total_size_bytes),
                    "size_bytes": total_size_bytes
                },
                "database": {
                    "size": format_bytes(db_size_bytes),
                    "size_bytes": db_size_bytes,
                    "table_count": table_count,
                    "table_sizes": table_sizes
                },
                "images": {
                    "size": format_bytes(estimated_image_size),
                    "size_bytes": estimated_image_size,
                    "file_count": images_count,
                    "total_urls": total_image_urls,
                    "unique_urls": len(unique_image_urls)
                },
                "crawler_results": {
                    "size": format_bytes(crawler_results_size_bytes),
                    "size_bytes": crawler_results_size_bytes,
                    "file_count": crawler_results_count
                }
            }
        }
        
    except Exception as e:
        logger.error(f"获取存储信息失败: {e}")
        return {
            "success": False,
            "data": {
                "error": str(e)
            }
        }

def get_forum_name(forum_id: str) -> str:
    """获取论坛名称"""
    forum_names = {
        "36": "亚洲无码",
        "37": "亚洲有码", 
        "2": "国产原创",
        "103": "高清中文字幕",
        "104": "素人原创",
        "39": "动漫原创",
        "152": "韩国主播"
    }
    return forum_names.get(forum_id, f"未知论坛({forum_id})")
