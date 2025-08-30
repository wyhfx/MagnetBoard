#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务管理器
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from croniter import croniter
import pytz

from models_scheduler import ScheduledTask
from new_crawler_manager import get_crawler_manager

logger = logging.getLogger(__name__)

class SchedulerManager:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.running_tasks: Dict[int, asyncio.Task] = {}
        self.scheduler_running = False
        
    def create_task(self, task_data: dict) -> ScheduledTask:
        """创建定时任务"""
        try:
            task = ScheduledTask(
                name=task_data["name"],
                description=task_data.get("description", ""),
                forum_id=task_data["forum_id"],
                start_page=task_data["start_page"],
                end_page=task_data["end_page"],
                keywords=",".join(task_data.get("keywords", [])),
                delay_between_pages=task_data.get("delay_between_pages", 2),
                max_concurrent=task_data.get("max_concurrent", 5),
                cron_expression=task_data["cron_expression"],
                timezone=task_data.get("timezone", "Asia/Shanghai"),
                enabled=task_data.get("enabled", True)
            )
            
            # 计算下次运行时间
            task.next_run = self._calculate_next_run(task.cron_expression, task.timezone)
            
            self.db.add(task)
            self.db.commit()
            
            logger.info(f"创建定时任务: {task.name}")
            return task
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建定时任务失败: {e}")
            raise
    
    def update_task(self, task_id: int, task_data: dict) -> Optional[ScheduledTask]:
        """更新定时任务"""
        try:
            task = self.db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if not task:
                return None
            
            # 更新字段
            for key, value in task_data.items():
                if hasattr(task, key):
                    if key == "keywords" and isinstance(value, list):
                        setattr(task, key, ",".join(value))
                    else:
                        setattr(task, key, value)
            
            # 重新计算下次运行时间
            task.next_run = self._calculate_next_run(task.cron_expression, task.timezone)
            
            self.db.commit()
            
            logger.info(f"更新定时任务: {task.name}")
            return task
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新定时任务失败: {e}")
            raise
    
    def delete_task(self, task_id: int) -> bool:
        """删除定时任务"""
        try:
            task = self.db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if not task:
                return False
            
            # 停止运行中的任务
            if task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()
                del self.running_tasks[task_id]
            
            self.db.delete(task)
            self.db.commit()
            
            logger.info(f"删除定时任务: {task.name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除定时任务失败: {e}")
            raise
    
    def get_task(self, task_id: int) -> Optional[ScheduledTask]:
        """获取定时任务"""
        return self.db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    
    def get_all_tasks(self) -> List[ScheduledTask]:
        """获取所有定时任务"""
        return self.db.query(ScheduledTask).order_by(ScheduledTask.created_at.desc()).all()
    
    def get_enabled_tasks(self) -> List[ScheduledTask]:
        """获取启用的定时任务"""
        return self.db.query(ScheduledTask).filter(ScheduledTask.enabled == True).all()
    
    def toggle_task(self, task_id: int) -> Optional[ScheduledTask]:
        """切换任务启用状态"""
        try:
            task = self.db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if not task:
                return None
            
            task.enabled = not task.enabled
            if task.enabled:
                task.next_run = self._calculate_next_run(task.cron_expression, task.timezone)
            
            self.db.commit()
            
            logger.info(f"切换任务状态: {task.name} -> {'启用' if task.enabled else '禁用'}")
            return task
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"切换任务状态失败: {e}")
            raise
    
    def _calculate_next_run(self, cron_expression: str, timezone: str) -> datetime:
        """计算下次运行时间"""
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            cron = croniter(cron_expression, now)
            return cron.get_next(datetime)
        except Exception as e:
            logger.error(f"计算下次运行时间失败: {e}")
            return datetime.now() + timedelta(hours=1)
    
    async def run_task(self, task: ScheduledTask):
        """运行定时任务"""
        try:
            logger.info(f"开始运行定时任务: {task.name}")
            
            # 更新任务状态
            task.last_run = datetime.utcnow()
            task.run_count += 1
            self.db.commit()
            
            # 获取爬虫管理器
            crawler_manager = get_crawler_manager()
            
            # 准备爬虫参数
            keywords = task.keywords.split(',') if task.keywords else None
            
            # 运行爬虫
            result = await crawler_manager.start_crawler(
                fid=task.forum_id,
                start_page=task.start_page,
                end_page=task.end_page,
                keywords=keywords,
                delay_between_pages=task.delay_between_pages
            )
            
            # 更新任务结果
            if result.get("success"):
                task.success_count += 1
                task.last_result = f"成功爬取 {result.get('data', {}).get('count', 0)} 个帖子"
            else:
                task.error_count += 1
                task.last_error = result.get("message", "未知错误")
            
            # 计算下次运行时间
            task.next_run = self._calculate_next_run(task.cron_expression, task.timezone)
            self.db.commit()
            
            logger.info(f"定时任务运行完成: {task.name}")
            
        except Exception as e:
            logger.error(f"定时任务运行失败: {task.name} - {e}")
            
            # 更新错误信息
            task.error_count += 1
            task.last_error = str(e)
            task.next_run = self._calculate_next_run(task.cron_expression, task.timezone)
            self.db.commit()
    
    async def start_scheduler(self):
        """启动定时任务调度器"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        logger.info("启动定时任务调度器")
        
        while self.scheduler_running:
            try:
                # 获取启用的任务
                enabled_tasks = self.get_enabled_tasks()
                now = datetime.utcnow()
                
                for task in enabled_tasks:
                    # 检查是否需要运行
                    if task.next_run and task.next_run <= now:
                        # 检查任务是否已在运行
                        if task.id not in self.running_tasks or self.running_tasks[task.id].done():
                            # 创建新任务
                            loop = asyncio.get_event_loop()
                            self.running_tasks[task.id] = loop.create_task(self.run_task(task))
                
                # 清理已完成的任务
                completed_tasks = []
                for task_id, task in self.running_tasks.items():
                    if task.done():
                        completed_tasks.append(task_id)
                
                for task_id in completed_tasks:
                    del self.running_tasks[task_id]
                
                # 等待1分钟
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"定时任务调度器错误: {e}")
                await asyncio.sleep(60)
    
    def stop_scheduler(self):
        """停止定时任务调度器"""
        self.scheduler_running = False
        
        # 取消所有运行中的任务
        for task in self.running_tasks.values():
            task.cancel()
        
        self.running_tasks.clear()
        logger.info("停止定时任务调度器")
    
    async def run_task_now(self, task_id: int) -> bool:
        """立即运行指定任务"""
        try:
            task = self.get_task(task_id)
            if not task:
                return False
            
            await self.run_task(task)
            return True
            
        except Exception as e:
            logger.error(f"立即运行任务失败: {e}")
            return False

# 全局调度器实例
scheduler_manager = None

def get_scheduler_manager(db_session: Session) -> SchedulerManager:
    """获取全局调度器实例"""
    global scheduler_manager
    if scheduler_manager is None:
        scheduler_manager = SchedulerManager(db_session)
    return scheduler_manager
