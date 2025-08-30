#!/usr/bin/env python3
"""
日志管理API路由
"""
import asyncio
import json
from datetime import datetime
from collections import deque
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from db import get_db
from models_logs import LogEntry

router = APIRouter()

# ---- 全局：日志订阅者与缓冲区 ----
subscribers: set[asyncio.Queue] = set()
log_buffer = deque(maxlen=1000)  # 保存最近1000条日志

def _emit_to_subscribers(log: dict):
    """
    从任意同步上下文里安全地把日志推给所有订阅队列
    """
    if not subscribers:
        return
    
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # 如果当前线程没有running loop，使用事件循环
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    
    # 使用列表副本避免在迭代时修改集合
    current_subscribers = list(subscribers)
    for q in current_subscribers:
        try:
            # 使用call_soon_threadsafe确保线程安全
            loop.call_soon_threadsafe(q.put_nowait, log)
        except asyncio.QueueFull:
            # 队列已满，移除订阅者
            subscribers.discard(q)
        except Exception:
            # 其他异常，移除订阅者
            subscribers.discard(q)

@router.post("/api/logs")
def create_log(
    level: str = Form(...),
    message: str = Form(...),
    source: str = Form("system"),
    details: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """创建日志"""
    try:
        log_entry = LogEntry(
            level=level,
            message=message,
            source=source,
            details=details or {}
        )
        db.add(log_entry)
        db.commit()
        
        # 发射到实时流
        emit_log(level, message, source, details)
        
        return {"success": True, "message": "日志创建成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建日志失败: {str(e)}")

@router.get("/api/logs")
def get_logs(
    page: int = 1,
    page_size: int = 50,
    level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取日志列表"""
    try:
        query = db.query(LogEntry)
        
        # 按级别过滤
        if level:
            query = query.filter(LogEntry.level == level)
        
        # 按时间倒序排列
        query = query.order_by(desc(LogEntry.timestamp))
        
        # 分页
        total = query.count()
        logs = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # 转换为字典格式
        log_list = []
        for log in logs:
            # 转换时间为北京时间格式
            if log.timestamp:
                from datetime import timezone, timedelta
                beijing_tz = timezone(timedelta(hours=8))
                # 如果时间戳是UTC时间，转换为北京时间
                if log.timestamp.tzinfo is None:
                    # 假设是UTC时间
                    utc_time = log.timestamp.replace(tzinfo=timezone.utc)
                    beijing_time = utc_time.astimezone(beijing_tz)
                else:
                    beijing_time = log.timestamp.astimezone(beijing_tz)
                formatted_timestamp = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                formatted_timestamp = None
            
            log_dict = {
                "id": log.id,
                "timestamp": formatted_timestamp,
                "level": log.level,
                "message": log.message,
                "source": log.source,
                "details": log.details
            }
            log_list.append(log_dict)
        
        return {
            "success": True,
            "data": {
                "total": total,
                "data": log_list,
                "page": page,
                "page_size": page_size
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")

@router.get("/api/logs/stream")
async def stream_logs(request: Request, replay: int = 100):
    """
    SSE 日志流。可选参数 replay=100 先补发最近100条
    """
    q: asyncio.Queue = asyncio.Queue(maxsize=1000)  # 限制队列大小
    subscribers.add(q)

    async def event_gen():
        try:
            # 先补发最近日志（可选）
            replay_count = min(int(replay), 1000)  # 限制回放数量
            recent_logs = list(log_buffer)[-replay_count:]
            for item in recent_logs:
                if await request.is_disconnected():
                    return
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

            # 发送心跳保持连接
            from datetime import timezone, timedelta
            beijing_tz = timezone(timedelta(hours=8))
            beijing_time = datetime.now(beijing_tz)
            yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': beijing_time.strftime('%Y-%m-%d %H:%M:%S')}, ensure_ascii=False)}\n\n"

            # 实时接收新日志
            while True:
                if await request.is_disconnected():
                    break
                
                try:
                    # 使用超时避免无限等待
                    log = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield f"data: {json.dumps(log, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    # 发送心跳保持连接
                    from datetime import timezone, timedelta
                    beijing_tz = timezone(timedelta(hours=8))
                    beijing_time = datetime.now(beijing_tz)
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': beijing_time.strftime('%Y-%m-%d %H:%M:%S')}, ensure_ascii=False)}\n\n"
                except Exception as e:
                    # 发送错误信息
                    from datetime import timezone, timedelta
                    beijing_tz = timezone(timedelta(hours=8))
                    beijing_time = datetime.now(beijing_tz)
                    error_log = {
                        'type': 'error',
                        'timestamp': beijing_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'message': f'日志流错误: {str(e)}'
                    }
                    yield f"data: {json.dumps(error_log, ensure_ascii=False)}\n\n"
                    break
        finally:
            subscribers.discard(q)

    return StreamingResponse(
        event_gen(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "X-Accel-Buffering": "no"  # 禁用nginx缓冲
        }
    )

@router.delete("/api/logs")
def clear_logs(db: Session = Depends(get_db)):
    """清空日志"""
    try:
        db.query(LogEntry).delete()
        db.commit()
        return {"success": True, "message": "日志已清空"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"清空日志失败: {str(e)}")

@router.get("/api/logs/stats")
def get_log_stats(db: Session = Depends(get_db)):
    """获取日志统计信息"""
    try:
        total_count = db.query(LogEntry).count()
        
        # 按级别统计
        level_stats = db.query(
            LogEntry.level,
            db.func.count(LogEntry.id).label('count')
        ).group_by(LogEntry.level).all()
        
        level_data = {stat.level: stat.count for stat in level_stats}
        
        # 今日日志数
        today = datetime.now().date()
        today_count = db.query(LogEntry).filter(
            db.func.date(LogEntry.timestamp) == today
        ).count()
        
        return {
            "success": True,
            "data": {
                "total_count": total_count,
                "today_count": today_count,
                "level_stats": level_data
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志统计失败: {str(e)}")

# 导出日志发射函数，供其他模块使用
def emit_log(level: str, message: str, source: str = "system", details: Optional[dict] = None):
    """发射日志到所有订阅者"""
    # 使用北京时间
    from datetime import timezone, timedelta
    beijing_tz = timezone(timedelta(hours=8))
    beijing_time = datetime.now(beijing_tz)
    
    log_record = {
        "timestamp": beijing_time.strftime("%Y-%m-%d %H:%M:%S"),
        "level": level,
        "message": message,
        "source": source,
        "details": details or {}
    }
    
    # 添加到缓冲区
    log_buffer.append(log_record)
    
    # 推送给所有订阅者
    _emit_to_subscribers(log_record)
    
    # 保存到数据库
    try:
        from db import SessionLocal
        from models_logs import LogEntry
        
        db = SessionLocal()
        log_entry = LogEntry(
            level=level,
            message=message,
            source=source,
            details=details or {}
        )
        db.add(log_entry)
        db.commit()
        db.close()
    except Exception as e:
        # 如果数据库保存失败，只记录错误，不影响日志发射
        print(f"保存日志到数据库失败: {e}")
