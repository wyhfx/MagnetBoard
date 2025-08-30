#!/usr/bin/env python3
"""
PostgreSQL数据库初始化脚本
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

def create_database():
    """创建数据库"""
    # 连接到默认的postgres数据库
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        user="postgres",
        password="password",
        database="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    try:
        # 检查数据库是否存在
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='sehuatang_db'")
        exists = cursor.fetchone()
        
        if not exists:
            # 创建数据库
            cursor.execute("CREATE DATABASE sehuatang_db")
            print("✅ 数据库 sehuatang_db 创建成功")
        else:
            print("⚠️  数据库 sehuatang_db 已存在")
            
    except Exception as e:
        print(f"❌ 创建数据库失败: {e}")
    finally:
        cursor.close()
        conn.close()

def create_tables():
    """创建表"""
    from db import engine
    from models_magnet import Base
    from models_settings import Base as SettingsBase
    
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        SettingsBase.metadata.create_all(bind=engine)
        print("✅ 所有表创建成功")
    except Exception as e:
        print(f"❌ 创建表失败: {e}")

def main():
    """主函数"""
    print("🚀 初始化PostgreSQL数据库")
    print("=" * 50)
    
    # 1. 创建数据库
    print("1. 创建数据库...")
    create_database()
    
    # 2. 创建表
    print("\n2. 创建表...")
    create_tables()
    
    print("\n🎉 PostgreSQL数据库初始化完成！")
    print("\n下一步：")
    print("1. 确保PostgreSQL服务正在运行")
    print("2. 检查数据库连接配置")
    print("3. 运行 python main.py 启动应用")

if __name__ == "__main__":
    main()
