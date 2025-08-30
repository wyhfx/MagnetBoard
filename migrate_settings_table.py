#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置表迁移脚本
用于初始化系统设置表
"""

from sqlalchemy import text
from db import engine, SessionLocal
from models_settings import Setting

def create_settings_table():
    """创建设置表并初始化默认设置"""
    try:
        # 创建表
        from models_settings import Base
        Base.metadata.create_all(bind=engine)
        
        # 获取数据库会话
        db = SessionLocal()
        
        # 检查是否已有设置
        existing_settings = db.query(Setting).count()
        
        if existing_settings == 0:
            # 初始化默认设置
            default_settings = [
                {
                    "key": "crawler_enabled",
                    "value": "true",
                    "description": "爬虫功能开关"
                },
                {
                    "key": "max_concurrent_downloads",
                    "value": "5",
                    "description": "最大并发下载数"
                },
                {
                    "key": "download_timeout",
                    "value": "30",
                    "description": "下载超时时间（秒）"
                },
                {
                    "key": "proxy_enabled",
                    "value": "false",
                    "description": "代理功能开关"
                },
                {
                    "key": "log_level",
                    "value": "INFO",
                    "description": "日志级别"
                },
                {
                    "key": "auto_refresh_interval",
                    "value": "300",
                    "description": "自动刷新间隔（秒）"
                },
                {
                    "key": "max_search_results",
                    "value": "100",
                    "description": "最大搜索结果数"
                },
                {
                    "key": "image_download_enabled",
                    "value": "true",
                    "description": "图片下载功能开关"
                },
                {
                    "key": "database_backup_enabled",
                    "value": "true",
                    "description": "数据库备份功能开关"
                },
                {
                    "key": "system_notifications",
                    "value": "true",
                    "description": "系统通知开关"
                }
            ]
            
            # 插入默认设置
            for setting_data in default_settings:
                setting = Setting(
                    key=setting_data["key"],
                    value=setting_data["value"],
                    description=setting_data["description"]
                )
                db.add(setting)
            
            db.commit()
            print(f"✅ 已初始化 {len(default_settings)} 个默认设置")
        else:
            print(f"⚠️ 设置表已存在 {existing_settings} 条记录，跳过初始化")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 创建设置表失败: {e}")
        raise

if __name__ == "__main__":
    print("🚀 开始创建设置表...")
    create_settings_table()
    print("✅ 设置表创建完成")
