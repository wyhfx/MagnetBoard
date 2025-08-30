#!/usr/bin/env python3
"""
日志数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime
from db import Base  # 使用统一的Base

class LogEntry(Base):
    """日志条目模型"""
    __tablename__ = "log_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    level = Column(String(20), index=True)  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    source = Column(String(50), index=True)  # crawler, system, api, etc.
    details = Column(JSON, nullable=True)  # 额外详细信息
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "level": self.level,
            "message": self.message,
            "source": self.source,
            "details": self.details
        }
