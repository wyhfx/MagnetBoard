# db.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 数据库配置
# 支持Docker环境变量配置
def get_database_url():
    """获取数据库连接URL"""
    # 如果设置了完整的DATABASE_URL，直接使用
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    
    # 否则从各个环境变量构建
    host = os.getenv("DATABASE_HOST", "localhost")
    port = os.getenv("DATABASE_PORT", "5432")
    name = os.getenv("DATABASE_NAME", "sehuatang_dev")
    user = os.getenv("DATABASE_USER", "postgres")
    password = os.getenv("DATABASE_PASSWORD", "sehuatang123")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{name}?client_encoding=utf8&options=-c%20timezone=Asia/Shanghai"

DATABASE_URL = get_database_url()

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_pre_ping=True,  # 连接前ping检查
    echo=False  # 设置为True可以看到SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 导入所有模型以确保表被创建
from models_magnet import MagnetLink
from models_settings import Setting
from models_logs import LogEntry

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
