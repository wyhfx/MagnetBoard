#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
磁力链接数据库模型
"""

import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index, DECIMAL
from sqlalchemy.dialects.postgresql import JSON
from db import Base  # 使用统一的Base

class MagnetLink(Base):
    __tablename__ = "magnet_links"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), index=True)
    content = Column(Text)
    url = Column(String(500), unique=True, index=True)
    images = Column(Text)  # JSON格式存储图片链接列表
    magnets = Column(Text)  # JSON格式存储磁力链接列表
    code = Column(String(100), index=True)
    size = Column(String(50))
    is_uncensored = Column(Boolean, default=False)
    author = Column(String(200))  # 从content提取的女优
    forum_id = Column(String(10), index=True)  # 论坛ID
    forum_type = Column(String(20), index=True)  # 'standard_av' 或 'non_av'
    magnet_hash = Column(String(64), index=True)  # 用于去重的hash
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 新增视频信息字段
    duration = Column(String(20))  # 视频时长
    resolution = Column(String(20))  # 分辨率
    format = Column(String(20))  # 视频格式
    language = Column(String(50))  # 语言
    subtitles = Column(Boolean, default=False)  # 是否有字幕
    
    # 图片信息
    cover_url = Column(String(500))  # 封面图片URL
    screenshot_urls = Column(JSON)  # 截图URL数组
    poster_urls = Column(JSON)  # 海报URL数组
    
    # 标签和分类
    tags = Column(JSON)  # 标签数组
    categories = Column(JSON)  # 分类数组
    
    # 统计信息
    download_count = Column(Integer, default=0)  # 下载次数
    view_count = Column(Integer, default=0)  # 查看次数
    rating = Column(DECIMAL(3,2))  # 评分 (0.00-5.00)
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "images": self.images,
            "magnets": self.magnets,
            "code": self.code,
            "size": self.size,
            "is_uncensored": self.is_uncensored,
            "author": self.author,
            "forum_id": self.forum_id,
            "forum_type": self.forum_type,
            "magnet_hash": self.magnet_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "duration": self.duration,
            "resolution": self.resolution,
            "format": self.format,
            "language": self.language,
            "subtitles": self.subtitles,
            "cover_url": self.cover_url,
            "screenshot_urls": self.screenshot_urls,
            "poster_urls": self.poster_urls,
            "tags": self.tags,
            "categories": self.categories,
            "download_count": self.download_count,
            "view_count": self.view_count,
            "rating": float(self.rating) if self.rating else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        return cls(**data)

# 创建索引
Index('idx_magnet_hash', MagnetLink.magnet_hash)
Index('idx_forum_type', MagnetLink.forum_type)
Index('idx_code_forum', MagnetLink.code, MagnetLink.forum_id)
Index('idx_title', MagnetLink.title)
Index('idx_url', MagnetLink.url)
Index('idx_created_at', MagnetLink.created_at)
Index('idx_author', MagnetLink.author)
