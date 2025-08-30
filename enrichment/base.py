#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元数据结果基础类
"""

from dataclasses import dataclass
from typing import Optional, List

@dataclass
class MetaResult:
    """元数据结果"""
    code_norm: str
    code_display: str
    title: Optional[str] = None
    actresses: Optional[List[str]] = None
    studio: Optional[str] = None
    release_date: Optional[str] = None
    tags: Optional[List[str]] = None
    cover_url: Optional[str] = None
    source: str = "unknown"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "code_norm": self.code_norm,
            "code_display": self.code_display,
            "title": self.title,
            "actresses": self.actresses or [],
            "studio": self.studio,
            "release_date": self.release_date,
            "tags": self.tags or [],
            "cover_url": self.cover_url,
            "source": self.source
        }













