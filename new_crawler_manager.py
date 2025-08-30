#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新爬虫管理器
集成cookies自动管理和CF重试机制
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime
import logging
from pathlib import Path

from new import NewCrawlerController
from collect_cookies import collect_cookies

class NewCrawlerManager:
    def __init__(self, 
                 max_concurrent: int = 5,
                 proxy: Optional[str] = None,
                 cookies_file: str = "data/cookies.json",
                 save_dir: str = "data/crawler_results"):
        """
        初始化爬虫管理器
        
        Args:
            max_concurrent: 最大并发数
            proxy: 代理地址
            cookies_file: cookies文件路径
            save_dir: 结果保存目录
        """
        self.max_concurrent = max_concurrent
        self.proxy = proxy
        self.cookies_file = cookies_file
        self.save_dir = save_dir
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 爬虫状态
        self.is_running = False
        self.current_task = None
        self.crawler = None
        
        # 回调函数
        self.progress_callback = None
        self.log_callback = None
        self.status_callback = None
        
        # CF重试配置
        self.max_cf_retries = 3
        self.cf_retry_delay = 60  # 秒
        
        # Cookies自动管理
        self.auto_refresh_cookies = True
        self.cookies_refresh_interval = 3600  # 1小时自动刷新
        self.last_cookies_refresh = 0
        
        # Cookies自动管理
        self.auto_refresh_cookies = True
        self.cookies_refresh_interval = 3600  # 1小时自动刷新
        self.last_cookies_refresh = 0
        
    def set_progress_callback(self, callback: Callable):
        """设置进度回调"""
        self.progress_callback = callback
    
    def set_log_callback(self, callback: Callable):
        """设置日志回调"""
        self.log_callback = callback
    
    def set_status_callback(self, callback: Callable):
        """设置状态回调"""
        self.status_callback = callback
    
    def add_log(self, message: str, level: str = "INFO"):
        """添加日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        
        if level == "INFO":
            self.logger.info(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        
        if self.log_callback:
            try:
                self.log_callback(timestamp, level, message)
            except Exception as e:
                self.logger.error(f"日志回调执行失败: {e}")
    
    def update_status(self, status: str, data: Dict = None):
        """更新状态"""
        if self.status_callback:
            try:
                self.status_callback(status, data or {})
            except Exception as e:
                self.logger.error(f"状态回调执行失败: {e}")
    
    def should_refresh_cookies(self) -> bool:
        """检查是否需要刷新cookies"""
        if not self.auto_refresh_cookies:
            return False
        
        current_time = time.time()
        return (current_time - self.last_cookies_refresh) > self.cookies_refresh_interval
    
    async def collect_cookies_auto(self, headless: bool = True) -> bool:
        """自动收集cookies"""
        try:
            self.add_log("开始自动收集cookies...")
            self.update_status("collecting_cookies", {"message": "正在收集cookies..."})
            
            success = await collect_cookies(headless=headless)
            
            if success:
                self.add_log("cookies收集成功")
                self.update_status("cookies_ready", {"message": "cookies收集完成"})
                self.last_cookies_refresh = time.time()
                return True
            else:
                self.add_log("cookies收集失败", "ERROR")
                self.update_status("cookies_failed", {"message": "cookies收集失败"})
                return False
                
        except Exception as e:
            self.add_log(f"收集cookies异常: {e}", "ERROR")
            self.update_status("cookies_error", {"message": f"cookies收集异常: {e}"})
            return False
    
    def should_refresh_cookies(self) -> bool:
        """检查是否需要刷新cookies"""
        if not self.auto_refresh_cookies:
            return False
        
        current_time = time.time()
        return (current_time - self.last_cookies_refresh) > self.cookies_refresh_interval
    
    async def ensure_fresh_cookies(self, force_refresh: bool = False) -> bool:
        """确保cookies是最新的"""
        # 检查是否需要刷新cookies
        if force_refresh or self.should_refresh_cookies():
            self.add_log("检测到cookies需要刷新，开始收集新cookies...")
            return await self.collect_cookies_auto(headless=True)
        
        # 检查cookies文件是否存在
        cookies_path = Path(self.cookies_file)
        if not cookies_path.exists():
            self.add_log("cookies文件不存在，开始收集cookies...")
            return await self.collect_cookies_auto(headless=True)
        
        # 检查cookies文件是否为空或损坏
        try:
            with open(cookies_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            if not cookies:
                self.add_log("cookies文件为空，开始收集cookies...")
                return await self.collect_cookies_auto(headless=True)
        except Exception as e:
            self.add_log(f"cookies文件损坏: {e}，开始收集cookies...")
            return await self.collect_cookies_auto(headless=True)
        
        return True
    
    async def test_connection_with_retry(self, force_cookies_refresh: bool = False) -> bool:
        """测试连接，如果失败则重试收集cookies"""
        for attempt in range(self.max_cf_retries + 1):
            try:
                # 确保cookies是最新的
                if not await self.ensure_fresh_cookies(force_refresh=force_cookies_refresh):
                    self.add_log("无法获取有效cookies", "ERROR")
                    return False
                
                if not self.crawler:
                    self.crawler = NewCrawlerController(
                        max_concurrent=self.max_concurrent,
                        proxy=self.proxy,
                        cookies_file=self.cookies_file,
                        save_dir=self.save_dir
                    )
                else:
                    # 重新加载cookies
                    await self.crawler.reload_cookies()
                
                # 设置回调
                if self.progress_callback:
                    self.crawler.set_progress_callback(self.progress_callback)
                if self.log_callback:
                    self.crawler.set_log_callback(self.log_callback)
                
                # 测试连接
                if await self.crawler.test_connection():
                    self.add_log("连接测试成功")
                    return True
                else:
                    self.add_log(f"连接测试失败，尝试 {attempt + 1}/{self.max_cf_retries + 1}")
                    
                    if attempt < self.max_cf_retries:
                        self.add_log("重新收集cookies...")
                        await self.collect_cookies_auto(headless=True)
                        
                        if attempt > 0:
                            self.add_log(f"等待 {self.cf_retry_delay} 秒后重试...")
                            await asyncio.sleep(self.cf_retry_delay)
                    
            except Exception as e:
                self.add_log(f"连接测试异常: {e}", "ERROR")
                if attempt < self.max_cf_retries:
                    await asyncio.sleep(self.cf_retry_delay)
        
        self.add_log("连接测试最终失败", "ERROR")
        return False
    
    async def start_crawler(self, 
                           fid: str, 
                           start_page: int = 1, 
                           end_page: int = 5,
                           keywords: Optional[List[str]] = None,
                           delay_between_pages: int = 2) -> Dict:
        """
        启动爬虫
        
        Args:
            fid: 论坛ID
            start_page: 开始页码
            end_page: 结束页码
            keywords: 关键词过滤
            delay_between_pages: 页面间延迟
            
        Returns:
            爬取结果
        """
        if self.is_running:
            return {"success": False, "message": "爬虫正在运行中"}
        
        self.is_running = True
        self.update_status("starting", {"message": "正在启动爬虫..."})
        
        try:
            # 启动前确保cookies是最新的
            if not await self.ensure_fresh_cookies():
                return {"success": False, "message": "无法获取有效cookies，启动失败"}
            
            # 测试连接，如果失败则重试收集cookies
            if not await self.test_connection_with_retry():
                return {"success": False, "message": "连接失败，无法启动爬虫"}
            
            self.update_status("crawling", {"message": "正在爬取..."})
            
            # 开始爬取，使用带重试的爬取方法
            threads = await self.crawl_with_retry(
                fid=fid,
                start_page=start_page,
                end_page=end_page,
                keywords=keywords,
                delay_between_pages=delay_between_pages
            )
            
            result = {
                "success": True,
                "message": f"爬取完成，共 {len(threads)} 个帖子",
                "data": {
                    "threads": threads,
                    "count": len(threads),
                    "fid": fid,
                    "start_page": start_page,
                    "end_page": end_page
                }
            }
            
            self.update_status("completed", result)
            return result
            
        except Exception as e:
            error_msg = f"爬取过程异常: {e}"
            self.add_log(error_msg, "ERROR")
            self.update_status("error", {"message": error_msg})
            return {"success": False, "message": error_msg}
        
        finally:
            self.is_running = False
    
    async def crawl_with_retry(self, 
                              fid: str, 
                              start_page: int, 
                              end_page: int,
                              keywords: Optional[List[str]] = None,
                              delay_between_pages: int = 2) -> List[Dict]:
        """带重试机制的爬取方法"""
        for attempt in range(self.max_cf_retries + 1):
            try:
                # 确保cookies是最新的
                if not await self.ensure_fresh_cookies():
                    self.add_log("无法获取有效cookies，跳过本次爬取", "ERROR")
                    return []
                
                # 重新加载cookies到爬虫
                if self.crawler:
                    await self.crawler.reload_cookies()
                
                # 开始爬取
                threads = await self.crawler.crawl_single_theme(
                    fid=fid,
                    start_page=start_page,
                    end_page=end_page,
                    keywords=keywords,
                    delay_between_pages=delay_between_pages
                )
                
                # 如果爬取成功，返回结果
                if threads:
                    self.add_log(f"爬取成功，获得 {len(threads)} 个帖子")
                    return threads
                else:
                    self.add_log("爬取未获得结果，可能是cookies过期", "WARNING")
                    
                    if attempt < self.max_cf_retries:
                        self.add_log("重新收集cookies并重试...")
                        await self.collect_cookies_auto(headless=True)
                        await asyncio.sleep(self.cf_retry_delay)
                    else:
                        self.add_log("达到最大重试次数，停止爬取")
                        return []
                        
            except Exception as e:
                self.add_log(f"爬取异常: {e}", "ERROR")
                
                if attempt < self.max_cf_retries:
                    self.add_log("重新收集cookies并重试...")
                    await self.collect_cookies_auto(headless=True)
                    await asyncio.sleep(self.cf_retry_delay)
                else:
                    self.add_log("达到最大重试次数，停止爬取")
                    return []
        
        return []
    
    def stop_crawler(self):
        """停止爬虫"""
        if self.crawler:
            self.crawler.stop_crawler()
        self.is_running = False
        self.update_status("stopped", {"message": "爬虫已停止"})
        self.add_log("爬虫停止命令已发送")
    
    async def get_crawler_status(self) -> Dict:
        """获取爬虫状态"""
        return {
            "is_running": self.is_running,
            "max_concurrent": self.max_concurrent,
            "proxy": self.proxy,
            "cookies_file": self.cookies_file,
            "save_dir": self.save_dir,
            "max_cf_retries": self.max_cf_retries,
            "auto_refresh_cookies": self.auto_refresh_cookies,
            "last_cookies_refresh": self.last_cookies_refresh,
            "cookies_refresh_interval": self.cookies_refresh_interval
        }
    
    def get_available_themes(self) -> Dict:
        """获取可用主题"""
        if self.crawler:
            return self.crawler.get_available_themes()
        else:
            # 返回默认主题配置
            return {
                "36": {"name": "亚洲无码", "fid": "36"},
                "37": {"name": "亚洲有码", "fid": "37"},
                "2": {"name": "国产原创", "fid": "2"},
                "103": {"name": "高清中文字幕", "fid": "103"},
                "104": {"name": "素人原创", "fid": "104"},
                "39": {"name": "动漫原创", "fid": "39"},
                "152": {"name": "韩国主播", "fid": "152"}
            }
    
    async def manual_refresh_cookies(self) -> bool:
        """手动刷新cookies"""
        return await self.collect_cookies_auto(headless=False)

# 全局爬虫管理器实例
crawler_manager = None

def get_crawler_manager() -> NewCrawlerManager:
    """获取全局爬虫管理器实例"""
    global crawler_manager
    if crawler_manager is None:
        crawler_manager = NewCrawlerManager()
    return crawler_manager
