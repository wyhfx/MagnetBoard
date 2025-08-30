#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务API路由
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from db import get_db
from models_scheduler import ScheduledTask
from scheduler_manager import get_scheduler_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/scheduler/tasks")
def get_scheduled_tasks(db: Session = Depends(get_db)):
    """获取所有定时任务"""
    try:
        scheduler = get_scheduler_manager(db)
        tasks = scheduler.get_all_tasks()
        
        return {
            "success": True,
            "data": [task.to_dict() for task in tasks]
        }
        
    except Exception as e:
        logger.error(f"获取定时任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取定时任务失败: {str(e)}")

@router.get("/api/scheduler/tasks/{task_id}")
def get_scheduled_task(task_id: int, db: Session = Depends(get_db)):
    """获取指定定时任务"""
    try:
        scheduler = get_scheduler_manager(db)
        task = scheduler.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="定时任务不存在")
        
        return {
            "success": True,
            "data": task.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取定时任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取定时任务失败: {str(e)}")

@router.post("/api/scheduler/tasks")
def create_scheduled_task(task_data: dict, db: Session = Depends(get_db)):
    """创建定时任务"""
    try:
        scheduler = get_scheduler_manager(db)
        task = scheduler.create_task(task_data)
        
        return {
            "success": True,
            "message": "定时任务创建成功",
            "data": task.to_dict()
        }
        
    except Exception as e:
        logger.error(f"创建定时任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建定时任务失败: {str(e)}")

@router.put("/api/scheduler/tasks/{task_id}")
def update_scheduled_task(task_id: int, task_data: dict, db: Session = Depends(get_db)):
    """更新定时任务"""
    try:
        scheduler = get_scheduler_manager(db)
        task = scheduler.update_task(task_id, task_data)
        
        if not task:
            raise HTTPException(status_code=404, detail="定时任务不存在")
        
        return {
            "success": True,
            "message": "定时任务更新成功",
            "data": task.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新定时任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新定时任务失败: {str(e)}")

@router.delete("/api/scheduler/tasks/{task_id}")
def delete_scheduled_task(task_id: int, db: Session = Depends(get_db)):
    """删除定时任务"""
    try:
        scheduler = get_scheduler_manager(db)
        success = scheduler.delete_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="定时任务不存在")
        
        return {
            "success": True,
            "message": "定时任务删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除定时任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除定时任务失败: {str(e)}")

@router.post("/api/scheduler/tasks/{task_id}/toggle")
def toggle_scheduled_task(task_id: int, db: Session = Depends(get_db)):
    """切换定时任务启用状态"""
    try:
        scheduler = get_scheduler_manager(db)
        task = scheduler.toggle_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="定时任务不存在")
        
        return {
            "success": True,
            "message": f"定时任务已{'启用' if task.enabled else '禁用'}",
            "data": task.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换定时任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"切换定时任务状态失败: {str(e)}")

@router.post("/api/scheduler/tasks/{task_id}/run")
async def run_scheduled_task_now(task_id: int, db: Session = Depends(get_db)):
    """立即运行定时任务"""
    try:
        scheduler = get_scheduler_manager(db)
        success = await scheduler.run_task_now(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="定时任务不存在")
        
        return {
            "success": True,
            "message": "定时任务已开始运行"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"立即运行定时任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"立即运行定时任务失败: {str(e)}")

@router.post("/api/scheduler/start")
async def start_scheduler(db: Session = Depends(get_db)):
    """启动定时任务调度器"""
    try:
        scheduler = get_scheduler_manager(db)
        await scheduler.start_scheduler()
        
        return {
            "success": True,
            "message": "定时任务调度器已启动"
        }
        
    except Exception as e:
        logger.error(f"启动定时任务调度器失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动定时任务调度器失败: {str(e)}")

@router.post("/api/scheduler/stop")
def stop_scheduler(db: Session = Depends(get_db)):
    """停止定时任务调度器"""
    try:
        scheduler = get_scheduler_manager(db)
        scheduler.stop_scheduler()
        
        return {
            "success": True,
            "message": "定时任务调度器已停止"
        }
        
    except Exception as e:
        logger.error(f"停止定时任务调度器失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止定时任务调度器失败: {str(e)}")

@router.get("/api/scheduler/status")
def get_scheduler_status(db: Session = Depends(get_db)):
    """获取定时任务调度器状态"""
    try:
        scheduler = get_scheduler_manager(db)
        
        enabled_tasks = scheduler.get_enabled_tasks()
        all_tasks = scheduler.get_all_tasks()
        
        return {
            "success": True,
            "data": {
                "scheduler_running": scheduler.scheduler_running,
                "total_tasks": len(all_tasks),
                "enabled_tasks": len(enabled_tasks),
                "running_tasks": len(scheduler.running_tasks),
                "tasks": [task.to_dict() for task in all_tasks]
            }
        }
        
    except Exception as e:
        logger.error(f"获取定时任务调度器状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取定时任务调度器状态失败: {str(e)}")
