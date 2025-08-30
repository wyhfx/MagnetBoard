#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置管理数据模型
"""

import json
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from db import Base  # 使用统一的Base

class Setting(Base):
    """设置表"""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, comment="设置键")
    value = Column(Text, comment="设置值")
    description = Column(String(200), comment="设置描述")
    category = Column(String(50), comment="设置分类")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

# 默认设置配置
DEFAULT_SETTINGS = [
    # 数据源配置
    {"key": "datasource", "value": "metatube", "description": "优先数据源", "category": "datasource"},
    {"key": "metatube_provider", "value": "", "description": "MetaTube Provider", "category": "datasource"},
    {"key": "metatube_fallback", "value": "true", "description": "是否启用 Fallback", "category": "datasource"},
    {"key": "metatube_url", "value": "http://192.168.31.102:8080", "description": "MetaTube 服务地址", "category": "datasource"},
    
    # 翻译配置
    {"key": "translate_enabled", "value": "false", "description": "启用翻译功能", "category": "translate"},
    {"key": "trans_provider", "value": "baidu", "description": "翻译服务提供商", "category": "translate"},
    {"key": "baidu_appid", "value": "", "description": "百度翻译 AppID", "category": "translate"},
    {"key": "baidu_key", "value": "", "description": "百度翻译密钥", "category": "translate"},
    
    # 代理配置
    {"key": "proxy_enabled", "value": "false", "description": "启用代理功能", "category": "proxy"},
    {"key": "proxy_host", "value": "", "description": "代理服务器地址", "category": "proxy"},
    {"key": "proxy_port", "value": "", "description": "代理服务器端口", "category": "proxy"},
    {"key": "proxy_username", "value": "", "description": "代理用户名", "category": "proxy"},
    {"key": "proxy_password", "value": "", "description": "代理密码", "category": "proxy"},
    {"key": "http_proxy", "value": "", "description": "HTTP 代理", "category": "proxy"},
    {"key": "https_proxy", "value": "", "description": "HTTPS 代理", "category": "proxy"},
    {"key": "no_proxy", "value": "localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12", "description": "不使用代理的地址", "category": "proxy"},
    
    # 下载器配置 - 统一使用downloader分类
    {"key": "downloader_enabled", "value": "false", "description": "启用下载器推送功能", "category": "downloader"},
    {"key": "downloader_type", "value": "qbittorrent", "description": "下载器类型", "category": "downloader"},
    
    # qBittorrent 配置
    {"key": "qbittorrent_enabled", "value": "false", "description": "启用qBittorrent", "category": "qbittorrent"},
    {"key": "qbittorrent_url", "value": "http://192.168.31.250:3020/", "description": "qBittorrent地址", "category": "qbittorrent"},
    {"key": "qbittorrent_username", "value": "admin", "description": "qBittorrent用户名", "category": "qbittorrent"},
    {"key": "qbittorrent_password", "value": "15031049495a", "description": "qBittorrent密码", "category": "qbittorrent"},
    {"key": "qbittorrent_category", "value": "sehuatang", "description": "qBittorrent下载分类", "category": "qbittorrent"},
    {"key": "qbittorrent_save_path", "value": "/downloads/sht", "description": "qBittorrent保存路径", "category": "qbittorrent"},
    {"key": "qbittorrent_auto_start", "value": "true", "description": "qBittorrent自动开始下载", "category": "qbittorrent"},
    
    # Transmission 配置
    {"key": "transmission_enabled", "value": "false", "description": "启用Transmission", "category": "transmission"},
    {"key": "transmission_url", "value": "http://localhost:9091", "description": "Transmission地址", "category": "transmission"},
    {"key": "transmission_username", "value": "admin", "description": "Transmission用户名", "category": "transmission"},
    {"key": "transmission_password", "value": "", "description": "Transmission密码", "category": "transmission"},
    {"key": "transmission_category", "value": "sehuatang", "description": "Transmission下载分类", "category": "transmission"},
    {"key": "transmission_save_path", "value": "/downloads/sht", "description": "Transmission保存路径", "category": "transmission"},
    {"key": "transmission_auto_start", "value": "true", "description": "Transmission自动开始下载", "category": "transmission"},
    
    # Aria2 配置
    {"key": "aria2_enabled", "value": "false", "description": "启用Aria2", "category": "aria2"},
    {"key": "aria2_url", "value": "http://localhost:6800", "description": "Aria2地址", "category": "aria2"},
    {"key": "aria2_secret", "value": "", "description": "Aria2密钥", "category": "aria2"},
    {"key": "aria2_category", "value": "sehuatang", "description": "Aria2下载分类", "category": "aria2"},
    {"key": "aria2_save_path", "value": "/downloads/sht", "description": "Aria2保存路径", "category": "aria2"},
    {"key": "aria2_auto_start", "value": "true", "description": "Aria2自动开始下载", "category": "aria2"},
]
