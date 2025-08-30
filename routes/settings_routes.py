#!/usr/bin/env python3
"""
系统设置API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from db import get_db, engine
from models_settings import Setting
from settings_manager import SettingsManager
from downloader_manager import DownloaderFactory, DownloaderManager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    """获取系统设置"""
    try:
        settings_manager = SettingsManager(db)
        settings = settings_manager.get_all_settings()
        return {"success": True, "data": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取设置失败: {str(e)}")

@router.post("/api/settings")
def update_settings(settings: dict, db: Session = Depends(get_db)):
    """更新系统设置"""
    try:
        settings_manager = SettingsManager(db)
        for key, value in settings.items():
            settings_manager.set_setting(key, value)
        return {"success": True, "message": "设置更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新设置失败: {str(e)}")

@router.post("/api/settings/test-database")
def test_database_connection(db: Session = Depends(get_db)):
    """测试数据库连接"""
    try:
        # 尝试执行一个简单的查询来测试连接
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            return {
                "success": True, 
                "message": "数据库连接成功",
                "data": {
                    "connected": True,
                    "database_type": "PostgreSQL"
                }
            }
        else:
            return {
                "success": False,
                "message": "数据库连接测试失败",
                "data": {
                    "connected": False,
                    "error": "查询返回异常结果"
                }
            }
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return {
            "success": False,
            "message": f"数据库连接失败: {str(e)}",
            "data": {
                "connected": False,
                "error": str(e)
            }
        }

@router.get("/api/settings/database-info")
def get_database_info(db: Session = Depends(get_db)):
    """获取数据库信息"""
    try:
        # 获取数据库版本
        version_result = db.execute(text("SELECT version()")).scalar()
        
        # 获取数据库名称
        db_name_result = db.execute(text("SELECT current_database()")).scalar()
        
        # 获取当前用户
        user_result = db.execute(text("SELECT current_user")).scalar()
        
        # 获取连接信息
        connection_info = {
            "version": version_result,
            "database": db_name_result,
            "user": user_result,
            "host": "localhost",  # 默认值，实际应该从连接字符串获取
            "port": 5432
        }
        
        return {
            "success": True,
            "data": connection_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库信息失败: {str(e)}")

@router.post("/api/settings/test-downloader")
def test_downloader_connection(db: Session = Depends(get_db)):
    """测试下载器连接"""
    try:
        # 创建下载器实例，传递数据库会话
        downloader = DownloaderManager(db)
        
        # 测试连接
        result = downloader.test_connection()
        
        return {
            "success": result["success"],
            "message": result["message"],
            "data": result.get("data", {})
        }
    except Exception as e:
        logger.error(f"测试下载器连接失败: {e}")
        return {
            "success": False,
            "message": f"测试失败: {str(e)}",
            "data": {}
        }

@router.get("/api/settings/downloader-info")
def get_downloader_info(db: Session = Depends(get_db)):
    """获取下载器信息"""
    try:
        settings_manager = SettingsManager(db)
        settings = settings_manager.get_all_settings()
        
        # 创建下载器实例
        downloader = DownloaderFactory.create_downloader(settings)
        
        # 获取下载器信息
        result = downloader.get_downloader_info()
        
        return {
            "success": result["success"],
            "message": result["message"],
            "data": result.get("data", {})
        }
    except Exception as e:
        logger.error(f"获取下载器信息失败: {e}")
        return {
            "success": False,
            "message": f"获取信息失败: {str(e)}",
            "data": {}
        }
@router.post("/api/settings/test-proxy")
def test_proxy_connection(proxy_config: dict):
    """测试代理连接"""
    try:
        import requests
        from urllib.parse import urlparse
        
        logger.info(f"开始测试代理连接，配置: {proxy_config}")
        
        # 检查代理配置
        if not proxy_config.get("enabled"):
            # 测试直连
            test_url = "http://httpbin.org/ip"
            response = requests.get(test_url, timeout=10)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "直连测试成功（代理未启用）",
                    "data": {
                        "connected": True,
                        "ip": response.json().get("origin", "未知"),
                        "proxy_url": None,
                        "mode": "direct"
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"直连测试失败，状态码: {response.status_code}",
                    "data": {
                        "connected": False,
                        "error": f"HTTP {response.status_code}",
                        "mode": "direct"
                    }
                }
        
        # 检查代理配置是否完整
        if not proxy_config.get("host") or not proxy_config.get("port"):
            return {
                "success": False,
                "message": "代理配置不完整：请填写代理地址和端口",
                "data": {
                    "connected": False,
                    "error": "配置不完整",
                    "mode": "proxy"
                }
            }
        
        # 构建代理URL
        protocol = "http"
        if proxy_config.get("username") and proxy_config.get("password"):
            proxy_url = f"{protocol}://{proxy_config['username']}:{proxy_config['password']}@{proxy_config['host']}:{proxy_config['port']}"
        else:
            proxy_url = f"{protocol}://{proxy_config['host']}:{proxy_config['port']}"
        
        logger.info(f"使用代理URL: {proxy_url}")
        
        # 设置代理
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        
        # 测试连接
        test_url = "http://httpbin.org/ip"
        logger.info(f"测试URL: {test_url}")
        
        response = requests.get(test_url, proxies=proxies, timeout=10)
        
        if response.status_code == 200:
            ip_info = response.json().get("origin", "未知")
            logger.info(f"代理连接成功，IP: {ip_info}")
            return {
                "success": True,
                "message": f"代理连接成功，当前IP: {ip_info}",
                "data": {
                    "connected": True,
                    "ip": ip_info,
                    "proxy_url": proxy_url,
                    "mode": "proxy"
                }
            }
        else:
            logger.error(f"代理连接失败，状态码: {response.status_code}")
            return {
                "success": False,
                "message": f"代理连接失败，状态码: {response.status_code}",
                "data": {
                    "connected": False,
                    "error": f"HTTP {response.status_code}",
                    "mode": "proxy"
                }
            }
            
    except requests.exceptions.ProxyError as e:
        logger.error(f"代理错误: {e}")
        return {
            "success": False,
            "message": "代理连接失败：代理服务器无响应或配置错误",
            "data": {
                "connected": False,
                "error": str(e),
                "mode": "proxy"
            }
        }
    except requests.exceptions.Timeout as e:
        logger.error(f"连接超时: {e}")
        return {
            "success": False,
            "message": "代理连接超时，请检查代理服务器是否可用",
            "data": {
                "connected": False,
                "error": str(e),
                "mode": "proxy"
            }
        }
    except requests.exceptions.ConnectionError as e:
        logger.error(f"连接错误: {e}")
        return {
            "success": False,
            "message": "代理连接失败：无法连接到代理服务器",
            "data": {
                "connected": False,
                "error": str(e),
                "mode": "proxy"
            }
        }
    except Exception as e:
        logger.error(f"代理连接测试失败: {e}")
        return {
            "success": False,
            "message": f"代理连接测试失败: {str(e)}",
            "data": {
                "connected": False,
                "error": str(e),
                "mode": "proxy"
            }
        }
