#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化定时任务表
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/sehuatang_db')

def create_scheduler_table():
    """创建定时任务表"""
    try:
        print("开始初始化定时任务表...")
        # 创建数据库引擎
        engine = create_engine(DATABASE_URL)
        print("数据库引擎创建成功")
        
        # 创建会话
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        print("数据库会话创建成功")
        
        # 检查表是否存在
        print("检查定时任务表是否存在...")
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'scheduled_tasks'
            );
        """))
        
        table_exists = result.scalar()
        print(f"表存在状态: {table_exists}")
        
        if not table_exists:
            print("创建定时任务表...")
            # 创建定时任务表
            db.execute(text("""
                CREATE TABLE scheduled_tasks (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    forum_id VARCHAR(10) NOT NULL,
                    start_page INTEGER DEFAULT 1,
                    end_page INTEGER DEFAULT 5,
                    keywords TEXT,
                    delay_between_pages INTEGER DEFAULT 2,
                    max_concurrent INTEGER DEFAULT 5,
                    cron_expression VARCHAR(100) NOT NULL,
                    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
                    enabled BOOLEAN DEFAULT TRUE,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP,
                    run_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    last_result TEXT,
                    last_error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            print("表结构创建成功")
            
            # 创建索引
            print("创建索引...")
            db.execute(text("""
                CREATE INDEX idx_scheduled_tasks_enabled ON scheduled_tasks(enabled);
                CREATE INDEX idx_scheduled_tasks_next_run ON scheduled_tasks(next_run);
                CREATE INDEX idx_scheduled_tasks_forum_id ON scheduled_tasks(forum_id);
            """))
            print("索引创建成功")
            
            db.commit()
            print("✅ 定时任务表创建成功")
        else:
            print("ℹ️ 定时任务表已存在")
        
        db.close()
        print("数据库会话已关闭")
        
    except Exception as e:
        print(f"❌ 创建定时任务表失败: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
            print("数据库会话已回滚并关闭")

if __name__ == "__main__":
    create_scheduler_table()
