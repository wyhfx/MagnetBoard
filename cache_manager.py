#!/usr/bin/env python3
"""
内存缓存管理器
"""
import json
import logging
import time
from typing import Any, Optional, Dict, List

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        """初始化内存缓存"""
        self._cache = {}
        logger.info("✅ 内存缓存管理器初始化成功")
    
    def is_connected(self) -> bool:
        """检查缓存连接状态（始终返回True）"""
        return True
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存"""
        try:
            expire_time = time.time() + expire if expire else None
            self._cache[key] = (value, expire_time)
            return True
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            if key in self._cache:
                value, expire_time = self._cache[key]
                if expire_time is None or time.time() < expire_time:
                    return value
                else:
                    # 过期，删除缓存
                    del self._cache[key]
            return None
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            if key in self._cache:
                del self._cache[key]
            return True
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            if key in self._cache:
                value, expire_time = self._cache[key]
                if expire_time is None or time.time() < expire_time:
                    return True
                else:
                    # 过期，删除缓存
                    del self._cache[key]
            return False
        except Exception as e:
            logger.error(f"检查键存在失败 {key}: {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        try:
            if key in self._cache:
                value, _ = self._cache[key]
                self._cache[key] = (value, time.time() + seconds)
                return True
            return False
        except Exception as e:
            logger.error(f"设置过期时间失败 {key}: {e}")
            return False
    
    # 爬虫状态缓存
    def set_crawler_status(self, status: Dict) -> bool:
        """缓存爬虫状态"""
        return self.set("crawler:status", status, expire=3600)  # 1小时过期
    
    def get_crawler_status(self) -> Optional[Dict]:
        """获取爬虫状态缓存"""
        return self.get("crawler:status")
    
    # 热门数据缓存
    def set_hot_magnets(self, magnets: List[Dict]) -> bool:
        """缓存热门磁力链接"""
        return self.set("magnets:hot", magnets, expire=1800)  # 30分钟过期
    
    def get_hot_magnets(self) -> Optional[List[Dict]]:
        """获取热门磁力链接缓存"""
        return self.get("magnets:hot")
    
    # 搜索结果缓存
    def set_search_cache(self, query: str, results: List[Dict]) -> bool:
        """缓存搜索结果"""
        key = f"search:{hash(query)}"
        return self.set(key, results, expire=900)  # 15分钟过期
    
    def get_search_cache(self, query: str) -> Optional[List[Dict]]:
        """获取搜索结果缓存"""
        key = f"search:{hash(query)}"
        return self.get(key)
    
    # 仪表盘统计缓存
    def set_dashboard_stats(self, stats: Dict) -> bool:
        """缓存仪表盘统计"""
        return self.set("dashboard:stats", stats, expire=300)  # 5分钟过期
    
    def get_dashboard_stats(self) -> Optional[Dict]:
        """获取仪表盘统计缓存"""
        return self.get("dashboard:stats")

# 全局缓存管理器实例
cache_manager = CacheManager()

def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例"""
    return cache_manager
