#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务数据模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from db import Base  # 使用统一的Base

class ScheduledTask(Base):
    """定时任务表"""
    __tablename__ = "scheduled_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="任务名称")
    description = Column(Text, comment="任务描述")
    
    # 爬虫配置
    forum_id = Column(String(10), nullable=False, comment="论坛ID")
    start_page = Column(Integer, default=1, comment="起始页面")
    end_page = Column(Integer, default=5, comment="结束页面")
    keywords = Column(Text, comment="关键词过滤，逗号分隔")
    delay_between_pages = Column(Integer, default=2, comment="页面间延迟(秒)")
    max_concurrent = Column(Integer, default=5, comment="最大并发数")
    
    # 定时配置
    cron_expression = Column(String(100), nullable=False, comment="Cron表达式")
    timezone = Column(String(50), default="Asia/Shanghai", comment="时区")
    
    # 状态
    enabled = Column(Boolean, default=True, comment="是否启用")
    last_run = Column(DateTime, comment="上次运行时间")
    next_run = Column(DateTime, comment="下次运行时间")
    run_count = Column(Integer, default=0, comment="运行次数")
    success_count = Column(Integer, default=0, comment="成功次数")
    error_count = Column(Integer, default=0, comment="失败次数")
    
    # 结果
    last_result = Column(Text, comment="上次运行结果")
    last_error = Column(Text, comment="上次错误信息")
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "forum_id": self.forum_id,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "keywords": self.keywords.split(',') if self.keywords else [],
            "delay_between_pages": self.delay_between_pages,
            "max_concurrent": self.max_concurrent,
            "cron_expression": self.cron_expression,
            "timezone": self.timezone,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "last_result": self.last_result,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
