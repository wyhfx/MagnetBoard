#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新爬虫系统 - 支持封面图和所有图片分离
"""

import asyncio
import json
import os
import re
import time
from typing import Optional, Dict, List
from pathlib import Path
import httpx
from playwright.async_api import async_playwright
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime

# ==================== HTTP客户端模块 ====================
class CrawlerHttpClient:
    def __init__(self, 
                 max_concurrent: int = 5,
                 timeout: int = 30,
                 proxy: Optional[str] = None,
                 cookies_file: str = "data/cookies.json"):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        
        # 获取代理配置
        if proxy:
            self.proxy = proxy
        else:
            # 从环境变量获取代理
            self.proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        
        self.cookies_file = cookies_file
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 修正代理地址（在logger创建之后）
        if self.proxy and 'host.docker.internal' in self.proxy:
            self.proxy = self.proxy.replace('host.docker.internal', '192.168.31.85')
            self.logger.info(f"修正代理地址: {self.proxy}")
        
        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        }
        
        Path(cookies_file).parent.mkdir(parents=True, exist_ok=True)
        
    async def create_client(self) -> httpx.AsyncClient:
        limits = httpx.Limits(max_connections=self.max_concurrent)
        
        client = httpx.AsyncClient(
            http2=True,
            timeout=self.timeout,
            limits=limits,
            headers=self.default_headers,
            proxies=self.proxy if self.proxy else None,
            follow_redirects=True
        )
        
        cookies = await self.load_cookies()
        if cookies:
            client.cookies.update(cookies)
            self.logger.info(f"已加载 {len(cookies)} 个cookies")
        
        return client
    
    async def load_cookies(self) -> Dict:
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'r', encoding='utf-8') as f:
                    cookies_data = json.load(f)
                    cookies = {}
                    for cookie in cookies_data:
                        cookies[cookie.get('name', '')] = cookie.get('value', '')
                    return cookies
        except Exception as e:
            self.logger.warning(f"加载cookies失败: {e}")
        return {}
    
    async def save_cookies(self, cookies: List[Dict]):
        try:
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            self.logger.info(f"已保存 {len(cookies)} 个cookies")
        except Exception as e:
            self.logger.error(f"保存cookies失败: {e}")
    
    async def collect_cookies_with_playwright(self, target_url: str = "https://sehuatang.org"):
        self.logger.info("开始使用Playwright收集cookies...")
        
        # 配置浏览器启动参数
        browser_args = []
        if self.proxy:
            browser_args.extend([
                f'--proxy-server={self.proxy}',
                '--ignore-certificate-errors',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ])
        
        # 在Docker环境中强制使用headless模式
        is_docker = os.path.exists('/.dockerenv')
        headless = is_docker
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=headless,
                args=browser_args
            )
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(target_url, wait_until="networkidle")
                
                # 处理18+同意按钮
                selectors = ["button:has-text('同意')", "button:has-text('进入')"]
                for selector in selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                        await page.click(selector)
                        break
                    except:
                        continue
                
                await page.wait_for_timeout(5000)
                
                cookies = await context.cookies()
                await self.save_cookies(cookies)
                
                return cookies
                
            except Exception as e:
                self.logger.error(f"收集cookies失败: {e}")
                return []
            finally:
                await browser.close()
    
    async def request_with_semaphore(self, client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
        async with self.semaphore:
            try:
                response = await client.get(url, **kwargs)
                return response
            except Exception as e:
                self.logger.error(f"请求失败 {url}: {e}")
                raise
    
    async def close_client(self, client: httpx.AsyncClient):
        await client.aclose()

# ==================== 列表页解析器 ====================
class ListPageParser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://sehuatang.org"
        
        self.themes = {
            "36": {"name": "亚洲无码", "fid": "36"},
            "37": {"name": "亚洲有码", "fid": "37"},
            "2": {"name": "国产原创", "fid": "2"},
            "103": {"name": "高清中文字幕", "fid": "103"},
            "104": {"name": "素人原创", "fid": "104"},
            "39": {"name": "动漫原创", "fid": "39"},
            "152": {"name": "韩国主播", "fid": "152"}
        }
    
    def generate_list_urls(self, fid: str, page: int = 1) -> List[str]:
        urls = []
        
        # 方式1: forum-{fid}-{page}.html
        url1 = f"{self.base_url}/forum-{fid}-{page}.html"
        urls.append(url1)
        
        # 方式2: forum.php?mod=forumdisplay&fid={fid}&page={page}
        url2 = f"{self.base_url}/forum.php?mod=forumdisplay&fid={fid}&page={page}"
        urls.append(url2)
        
        return urls
    
    def parse_thread_links(self, html: str, source_url: str) -> List[Dict]:
        soup = BeautifulSoup(html, 'html.parser')
        threads = []
        
        selectors = [
            "a[href*='thread-']",
            "a[href*='forum.php?mod=viewthread']",
            ".tl a",
            ".s a",
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if not href:
                    continue
                
                tid = self.extract_tid(href)
                if not tid:
                    continue
                
                title = self.extract_title(link)
                if not title:
                    continue
                
                # 过滤明显是广告的帖子标题
                if self.is_advertisement_title(title):
                    continue
                
                full_url = urljoin(source_url, href)
                
                thread_info = {
                    'tid': tid,
                    'title': title,
                    'url': full_url,
                    'source_url': source_url
                }
                
                threads.append(thread_info)
        
        return threads
    
    def extract_tid(self, href: str) -> Optional[str]:
        match = re.search(r'thread-(\d+)', href)
        if match:
            return match.group(1)
        
        match = re.search(r'tid=(\d+)', href)
        if match:
            return match.group(1)
        
        return None
    
    def extract_title(self, link_element) -> Optional[str]:
        title = link_element.get('title', '')
        if title:
            return title.strip()
        
        title = link_element.get_text(strip=True)
        if title:
            return title
        
        for attr in ['alt', 'data-title']:
            title = link_element.get(attr, '')
            if title:
                return title.strip()
        
        return None
    
    def is_advertisement_title(self, title: str) -> bool:
        """检测标题是否为广告"""
        if not title:
            return True
        
        title_lower = title.lower()
        
        # 广告关键词
        ad_keywords = [
            '广告', '推广', '赞助', '合作', '商业', '营销',
            'ad', 'advertisement', 'sponsor', 'promotion', 'commercial',
            '推广链接', '广告位', '招商', '代理', '加盟',
            '赚钱', '致富', '兼职', '招聘', '求职',
            '游戏', '赌博', '博彩', '彩票', '时时彩',
            '贷款', '信用卡', '理财', '投资', '股票',
            '保健品', '减肥', '美容', '整形', '增高',
            '代购', '代刷', '代练', '代充', '代挂',
            '刷单', '刷钻', '刷信誉', '刷流量', '刷粉丝',
            '色情', '成人', '一夜情', '援交', '按摩',
            '办证', '刻章', '发票', '假证', '假文凭',
            '黑客', '破解', '盗号', '刷钻', '外挂'
        ]
        
        # 检查是否包含广告关键词
        for keyword in ad_keywords:
            if keyword in title_lower:
                return True
        
        # 检查标题长度（太短的可能是广告）
        if len(title.strip()) < 5:
            return True
        
        # 检查是否全是特殊字符
        if re.match(r'^[^\u4e00-\u9fff\w\s]+$', title):
            return True
        
        # 检查是否包含大量数字和特殊字符（可能是垃圾信息）
        if len(re.findall(r'[0-9]', title)) > len(title) * 0.3:
            return True
        
        return False
    
    def deduplicate_threads(self, threads: List[Dict]) -> List[Dict]:
        seen_tids = set()
        unique_threads = []
        
        for thread in threads:
            tid = thread.get('tid')
            if tid and tid not in seen_tids:
                seen_tids.add(tid)
                unique_threads.append(thread)
        
        self.logger.info(f"去重前: {len(threads)} 个帖子, 去重后: {len(unique_threads)} 个帖子")
        return unique_threads
    
    async def parse_list_page(self, client: httpx.AsyncClient, fid: str, page: int = 1) -> List[Dict]:
        urls = self.generate_list_urls(fid, page)
        all_threads = []
        
        responses = await asyncio.gather(*[
            self.request_page(client, url) for url in urls
        ], return_exceptions=True)
        
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                self.logger.error(f"请求失败 {urls[i]}: {response}")
                continue
            
            if response and response.status_code == 200:
                threads = self.parse_thread_links(response.text, urls[i])
                all_threads.extend(threads)
                self.logger.info(f"从 {urls[i]} 解析到 {len(threads)} 个帖子")
            else:
                self.logger.warning(f"请求失败 {urls[i]}: 状态码 {response.status_code if response else 'None'}")
        
        unique_threads = self.deduplicate_threads(all_threads)
        return unique_threads
    
    async def request_page(self, client: httpx.AsyncClient, url: str) -> Optional[httpx.Response]:
        try:
            response = await client.get(url)
            return response
        except Exception as e:
            self.logger.error(f"请求失败 {url}: {e}")
            return None
    
    def filter_threads_by_keywords(self, threads: List[Dict], keywords: List[str]) -> List[Dict]:
        if not keywords:
            return threads
        
        filtered_threads = []
        for thread in threads:
            title = thread.get('title', '').lower()
            for keyword in keywords:
                if keyword.lower() in title:
                    filtered_threads.append(thread)
                    break
        
        self.logger.info(f"关键词过滤: {len(threads)} -> {len(filtered_threads)}")
        return filtered_threads
    
    async def parse_thread_detail(self, client: httpx.AsyncClient, thread_url: str) -> Optional[Dict]:
        """解析帖子详情页面，提取磁力链接、番号等信息"""
        try:
            response = await client.get(thread_url)
            if response.status_code != 200:
                self.logger.warning(f"获取帖子详情失败: {thread_url}, 状态码: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取基本信息
            title = self.extract_thread_title(soup)
            content = self.extract_thread_content(soup)
            
            # 提取磁力链接
            magnets = self.extract_magnet_links(soup)
            
            # 提取番号
            code = self.extract_code(title, content)
            
            # 提取其他信息
            author = self.extract_author(soup)
            size = self.extract_size(content)
            is_uncensored = self.check_uncensored(title, content)
            
            # 检查是否有磁力链接，如果没有则跳过
            if not magnets:
                self.logger.info(f"跳过无磁力链接的帖子: {thread_url}")
                return None
            
            # 提取图片（分别提取封面图和所有图片）
            images = self.extract_images(soup)
            
            thread_detail = {
                'title': title,
                'content': content,
                'magnets': magnets,
                'code': code,
                'author': author,
                'size': size,
                'is_uncensored': is_uncensored,
                'images': images,
                'url': thread_url
            }
            
            return thread_detail
            
        except Exception as e:
            self.logger.error(f"解析帖子详情失败 {thread_url}: {e}")
            return None
    
    def extract_thread_title(self, soup) -> str:
        """提取帖子标题"""
        title_selectors = [
            'h1#thread_subject',
            'h1.thread_subject',
            'h1',
            '.thread_subject',
            'title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title:
                    return title
        
        return ""
    
    def extract_thread_content(self, soup) -> str:
        """提取帖子内容"""
        content_selectors = [
            'div.t_msgfont',
            'div.postmessage',
            '.t_msgfont',
            '.postmessage',
            'div[id*="post_"]'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content = element.get_text(strip=True)
                if content:
                    return content
        
        return ""
    
    def extract_magnet_links(self, soup) -> List[str]:
        """提取磁力链接"""
        magnets = []
        
        # 查找磁力链接 - 使用与旧系统一致的正则表达式
        magnet_pattern = r'magnet:\?xt=urn:btih:[0-9A-Fa-f]{40,}'
        
        # 从页面文本中提取
        page_text = soup.get_text()
        magnets = re.findall(magnet_pattern, page_text, re.IGNORECASE)
        
        # 从链接中提取
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if href.startswith('magnet:'):
                magnets.append(href)
        
        # 去重
        magnets = list(set(magnets))
        return magnets
    
    def extract_code(self, title: str, content: str) -> str:
        """提取番号"""
        # 常见的番号格式
        code_patterns = [
            r'[A-Z]{2,4}-\d{3,4}',  # 如 ABC-123, ABCD-1234
            r'[A-Z]{2,4}\d{3,4}',   # 如 ABC123, ABCD1234
            r'[A-Z]{2,4}-\d{2,3}',  # 如 ABC-12, ABCD-123
        ]
        
        text = f"{title} {content}"
        for pattern in code_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].upper()
        
        return ""
    
    def extract_author(self, soup) -> str:
        """提取女优信息 - 从帖子内容中提取结构化信息"""
        # 获取帖子内容文本
        content_text = ""
        content_selectors = [
            'div.t_msgfont',
            'div.postmessage',
            '.t_msgfont',
            '.postmessage',
            'div[id*="post_"]',
            'td.t_f'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content_text = element.get_text(strip=True)
                break
        
        if not content_text:
            return ""
        
        # 从内容中提取女优信息
        # 匹配【出演女优】：女优名称 格式
        actress_patterns = [
            r'【出演女优】：\s*([^\n\r【】]+)',
            r'【女优】：\s*([^\n\r【】]+)',
            r'【演员】：\s*([^\n\r【】]+)',
            r'出演女优[：:]\s*([^\n\r【】]+)',
            r'女优[：:]\s*([^\n\r【】]+)',
            r'演员[：:]\s*([^\n\r【】]+)'
        ]
        
        for pattern in actress_patterns:
            match = re.search(pattern, content_text)
            if match:
                actress = match.group(1).strip()
                # 清理女优名称
                actress = re.sub(r'[^\u4e00-\u9fff\w\s]', '', actress).strip()
                if actress and len(actress) > 1:
                    return actress
        
        return ""
    
    def extract_size(self, content: str) -> str:
        """提取文件大小 - 从帖子内容中提取结构化信息"""
        # 匹配【影片容量】：大小 格式
        size_patterns = [
            r'【影片容量】：\s*(\d+(?:\.\d+)?)\s*(GB|MB|KB|G|M|K)',
            r'【容量】：\s*(\d+(?:\.\d+)?)\s*(GB|MB|KB|G|M|K)',
            r'影片容量[：:]\s*(\d+(?:\.\d+)?)\s*(GB|MB|KB|G|M|K)',
            r'容量[：:]\s*(\d+(?:\.\d+)?)\s*(GB|MB|KB|G|M|K)',
            # 备用模式：直接匹配大小
            r'(\d+(?:\.\d+)?)\s*(GB|MB|KB|G|M|K)B?'
        ]
        
        for pattern in size_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                size, unit = matches[0]
                # 标准化单位
                unit = unit.upper()
                if unit in ["G", "GB"]:
                    return f"{size}GB"
                elif unit in ["M", "MB"]:
                    return f"{size}MB"
                elif unit in ["K", "KB"]:
                    return f"{size}KB"
        
        return ""
    
    def check_uncensored(self, title: str, content: str) -> bool:
        """检查是否为无码 - 从帖子内容中提取结构化信息"""
        # 首先尝试从结构化信息中提取
        text = f"{title} {content}"
        
        # 匹配【是否有码】：有码/无码 格式
        censored_patterns = [
            r'【是否有码】：\s*(无码|有码)',
            r'【有码】：\s*(无码|有码)',
            r'是否有码[：:]\s*(无码|有码)',
            r'有码[：:]\s*(无码|有码)'
        ]
        
        for pattern in censored_patterns:
            match = re.search(pattern, text)
            if match:
                status = match.group(1)
                return status == "无码"
        
        # 备用检测：关键词匹配
        uncensored_keywords = [
            "无码", "無碼", "uncensored", "无修正", "無修正",
            "流出", "破解", "破解版", "破解版流出"
        ]
        
        text_lower = text.lower()
        for keyword in uncensored_keywords:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def extract_images(self, soup) -> Dict[str, List[str]]:
        """提取图片链接 - 分别提取封面图和所有图片"""
        all_images = []  # 所有图片
        cover_images = []  # 封面图列表
        
        # 1. 提取所有图片
        content_selectors = [
            'td.t_f img',  # 旧系统使用的主要选择器
            'div.t_msgfont img',
            'div.postmessage img',
            '.t_msgfont img',
            '.postmessage img',
            'div[id*="post_"] img'
        ]
        
        for selector in content_selectors:
            imgs = soup.select(selector)
            for img in imgs:
                src = img.get('src') or img.get('data-src') or img.get('zoomfile') or img.get('file')
                if src:
                    # 处理相对URL
                    if not src.startswith('http'):
                        src = f"https://sehuatang.org{src}" if src.startswith('/') else f"https://sehuatang.org/{src}"
                    
                    # 只保留jpg格式的图片，并过滤广告
                    if (src.lower().endswith('.jpg') or src.lower().endswith('.jpeg')) and (
                        'none.gif' not in src and 
                        'placeholder' not in src and
                        'static/image/common' not in src and
                        'avatar' not in src and
                        'logo' not in src and
                        'icon' not in src and
                        'btn' not in src and
                        'torrent.gif' not in src and  # 排除种子文件图标
                        'ad' not in src.lower() and  # 排除广告
                        'banner' not in src.lower() and  # 排除横幅
                        'sponsor' not in src.lower() and  # 排除赞助
                        'ads' not in src.lower() and  # 排除广告
                        'advertisement' not in src.lower() and  # 排除广告
                        'promo' not in src.lower() and  # 排除推广
                        'commercial' not in src.lower() and  # 排除商业广告
                        'tuiguang' not in src.lower() and  # 排除推广
                        'guanggao' not in src.lower()  # 排除广告
                    ):
                        if src not in all_images:
                            all_images.append(src)
        
        # 2. 查找附件链接中的图片
        content_elements = soup.select('td.t_f, div.t_msgfont, div.postmessage')
        for content_elem in content_elements:
            attachment_links = content_elem.find_all('a', href=True)
            for link in attachment_links:
                href = link.get('href', '')
                link_text = link.get_text(strip=True)
                
                # 只查找jpg格式的图片附件链接
                if href.lower().endswith('.jpg') or href.lower().endswith('.jpeg'):
                    if not href.startswith('http'):
                        href = f"https://sehuatang.org{href}" if href.startswith('/') else f"https://sehuatang.org/{href}"
                    if href not in all_images:
                        all_images.append(href)
        
        # 3. 从所有图片中筛选封面图
        for img_url in all_images:
            # 检查是否是封面图（文件名格式）
            if re.search(r'[A-Z]{2,4}-\d{3,4}', img_url, re.IGNORECASE):
                if img_url not in cover_images:
                    cover_images.append(img_url)
        
        # 4. 返回结果
        return {
            "cover_images": cover_images[:2],  # 封面图最多2张
            "all_images": all_images  # 所有图片
        }
    
    def get_theme_info(self, fid: str) -> Optional[Dict]:
        return self.themes.get(fid)
    
    def get_all_theme_ids(self) -> List[str]:
        return list(self.themes.keys())

# ==================== 主爬虫控制器 ====================
class NewCrawlerController:
    def __init__(self, 
                 max_concurrent: int = 5,
                 proxy: Optional[str] = None,
                 cookies_file: str = "data/cookies.json",
                 save_dir: str = "data/crawler_results"):
        self.max_concurrent = max_concurrent
        self.proxy = proxy
        self.cookies_file = cookies_file
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        self.http_client = CrawlerHttpClient(
            max_concurrent=max_concurrent,
            proxy=proxy,
            cookies_file=cookies_file
        )
        self.parser = ListPageParser()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.progress_callback = None
        self.log_callback = None
        self.is_running = False
        
    def set_progress_callback(self, callback):
        self.progress_callback = callback
    
    def set_log_callback(self, callback):
        self.log_callback = callback
    
    def add_log(self, message: str, level: str = "INFO"):
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
    
    async def collect_cookies(self) -> bool:
        try:
            self.add_log("开始收集cookies...")
            cookies = await self.http_client.collect_cookies_with_playwright()
            if cookies:
                self.add_log(f"成功收集 {len(cookies)} 个cookies")
                return True
            else:
                self.add_log("cookies收集失败", "ERROR")
                return False
        except Exception as e:
            self.add_log(f"收集cookies异常: {e}", "ERROR")
            return False
    
    async def crawl_single_theme(self, 
                                fid: str, 
                                start_page: int = 1, 
                                end_page: int = 5,
                                keywords: Optional[List[str]] = None,
                                delay_between_pages: int = 2) -> List[Dict]:
        """爬取单个主题的页面"""
        if self.is_running:
            self.add_log("爬虫正在运行中，请等待完成", "WARNING")
            return []
        
        self.is_running = True
        all_threads = []
        
        try:
            client = await self.http_client.create_client()
            
            theme_info = self.parser.get_theme_info(fid)
            theme_name = theme_info.get('name', f'论坛{fid}') if theme_info else f'论坛{fid}'
            
            self.add_log(f"开始爬取 {theme_name} (FID: {fid})")
            self.add_log(f"爬取范围: 第{start_page}页 - 第{end_page}页")
            self.add_log(f"页面间延迟: {delay_between_pages}秒")
            
            total_pages = end_page - start_page + 1
            
            for page in range(start_page, end_page + 1):
                if not self.is_running:
                    self.add_log("爬虫被停止", "WARNING")
                    break
                
                try:
                    self.add_log(f"正在爬取第 {page} 页...")
                    
                    threads = await self.parser.parse_list_page(client, fid, page)
                    
                    if threads:
                        all_threads.extend(threads)
                        self.add_log(f"第 {page} 页解析到 {len(threads)} 个帖子")
                    else:
                        self.add_log(f"第 {page} 页未解析到帖子", "WARNING")
                    
                    if self.progress_callback:
                        progress = (page - start_page + 1) / total_pages * 100
                        self.progress_callback(progress, f"第 {page} 页完成")
                    
                    # 页面间延迟，避免请求过快
                    if page < end_page:
                        self.add_log(f"等待 {delay_between_pages} 秒后继续...")
                        await asyncio.sleep(delay_between_pages)
                    
                except Exception as e:
                    self.add_log(f"爬取第 {page} 页失败: {e}", "ERROR")
                    continue
            
            unique_threads = self.parser.deduplicate_threads(all_threads)
            self.add_log(f"去重后共 {len(unique_threads)} 个帖子")
            
            if keywords:
                filtered_threads = self.parser.filter_threads_by_keywords(unique_threads, keywords)
                self.add_log(f"关键词过滤后 {len(filtered_threads)} 个帖子")
                unique_threads = filtered_threads
            
            # 爬取帖子详情并保存到数据库
            detailed_threads = await self.crawl_thread_details(client, unique_threads, fid)
            
            await self.save_results(detailed_threads, fid, theme_name)
            
            return detailed_threads
            
        except Exception as e:
            self.add_log(f"爬取过程异常: {e}", "ERROR")
            return []
        finally:
            if 'client' in locals():
                await self.http_client.close_client(client)
            self.is_running = False
    
    async def save_to_database(self, thread: Dict, fid: str):
        """保存帖子信息到数据库"""
        try:
            from db import SessionLocal
            from models_magnet import MagnetLink
            
            db = SessionLocal()
            
            # 检查是否已存在
            existing = db.query(MagnetLink).filter(
                MagnetLink.magnet_hash == thread.get('tid', '')
            ).first()
            
            if existing:
                self.add_log(f"帖子已存在，跳过: {thread.get('title', 'Unknown')}")
                db.close()
                return
            
            # 处理图片数据
            images_data = thread.get('images', {})
            cover_images = images_data.get('cover_images', [])
            all_images = images_data.get('all_images', [])
            
            # 设置封面图URL（取第一张封面图）
            cover_url = cover_images[0] if cover_images else None
            
            # 创建新的磁力链接记录
            magnet_link = MagnetLink(
                title=thread.get('title', ''),
                content=thread.get('content', ''),
                code=thread.get('code', ''),
                author=thread.get('author', ''),
                size=thread.get('size', ''),
                is_uncensored=thread.get('is_uncensored', False),
                forum_id=fid,
                forum_type=self.parser.get_theme_info(fid).get('name', '') if self.parser.get_theme_info(fid) else '',
                magnet_hash=thread.get('tid', ''),
                url=thread.get('url', ''),
                magnets=json.dumps(thread.get('magnets', []), ensure_ascii=False),
                images=json.dumps(all_images, ensure_ascii=False),  # 保存所有图片
                cover_url=cover_url,  # 保存封面图URL
            )
            
            db.add(magnet_link)
            db.commit()
            
            self.add_log(f"保存到数据库成功: {thread.get('code', 'Unknown')} - {thread.get('title', 'Unknown')}")
            
            db.close()
            
        except Exception as e:
            self.add_log(f"保存到数据库失败: {e}", "ERROR")
    
    async def crawl_thread_details(self, client: httpx.AsyncClient, threads: List[Dict], fid: str) -> List[Dict]:
        """爬取帖子详情并保存到数据库"""
        detailed_threads = []
        total_threads = len(threads)
        
        self.add_log(f"开始爬取 {total_threads} 个帖子的详细信息...")
        
        for i, thread in enumerate(threads):
            if not self.is_running:
                self.add_log("爬虫被停止", "WARNING")
                break
            
            try:
                thread_url = thread.get('url')
                if not thread_url:
                    continue
                
                self.add_log(f"爬取帖子详情 {i+1}/{total_threads}: {thread.get('title', 'Unknown')}")
                
                # 爬取帖子详情
                detail = await self.parser.parse_thread_detail(client, thread_url)
                
                if detail:
                    # 检查是否有磁力链接
                    magnets = detail.get('magnets', [])
                    if not magnets:
                        self.add_log(f"跳过无磁力链接的帖子: {thread_url}")
                        continue
                    
                    # 合并基本信息
                    thread.update(detail)
                    
                    # 保存到数据库
                    await self.save_to_database(thread, fid)
                    
                    detailed_threads.append(thread)
                    self.add_log(f"帖子详情爬取成功: {detail.get('code', 'Unknown')} - {len(magnets)} 个磁力链接")
                else:
                    self.add_log(f"帖子详情爬取失败: {thread_url}", "WARNING")
                
                # 进度回调
                if self.progress_callback:
                    progress = (i + 1) / total_threads * 100
                    self.progress_callback(progress, f"详情爬取进度: {i+1}/{total_threads}")
                
                # 延迟，避免请求过快
                await asyncio.sleep(1)
                
            except Exception as e:
                self.add_log(f"爬取帖子详情失败 {thread.get('url', 'Unknown')}: {e}", "ERROR")
                continue
        
        self.add_log(f"帖子详情爬取完成，成功爬取 {len(detailed_threads)} 个帖子")
        return detailed_threads
    
    async def save_results(self, threads: List[Dict], fid: str, theme_name: str):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{theme_name}_{fid}_{timestamp}.json"
            filepath = self.save_dir / filename
            
            result_data = {
                "metadata": {
                    "theme_name": theme_name,
                    "fid": fid,
                    "crawl_time": datetime.now().isoformat(),
                    "total_threads": len(threads)
                },
                "threads": threads
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            self.add_log(f"结果已保存到: {filepath}")
            
        except Exception as e:
            self.add_log(f"保存结果失败: {e}", "ERROR")
    
    def stop_crawler(self):
        self.is_running = False
        self.add_log("爬虫停止命令已发送")
    
    async def reload_cookies(self):
        """重新加载cookies"""
        try:
            await self.http_client.load_cookies()
            self.add_log("cookies重新加载成功")
        except Exception as e:
            self.add_log(f"重新加载cookies失败: {e}", "ERROR")
    
    async def get_crawler_status(self) -> Dict:
        return {
            "is_running": self.is_running,
            "max_concurrent": self.max_concurrent,
            "proxy": self.proxy,
            "cookies_file": self.cookies_file,
            "save_dir": str(self.save_dir)
        }
    
    def get_available_themes(self) -> Dict:
        return self.parser.themes
    
    async def test_connection(self) -> bool:
        try:
            client = await self.http_client.create_client()
            response = await self.http_client.request_with_semaphore(
                client, "https://sehuatang.org"
            )
            await self.http_client.close_client(client)
            
            if response and response.status_code == 200:
                self.add_log("连接测试成功")
                return True
            else:
                self.add_log("连接测试失败", "ERROR")
                return False
        except Exception as e:
            self.add_log(f"连接测试异常: {e}", "ERROR")
            return False


# ==================== 测试函数 ====================
async def test_new_crawler():
    """测试新爬虫系统"""
    print("🚀 开始测试新爬虫系统...")
    
    # 创建爬虫控制器
    crawler = NewCrawlerController(
        max_concurrent=3,
        proxy=None,  # 设置代理如 "http://127.0.0.1:7890"
        cookies_file="data/cookies.json"
    )
    
    # 测试连接
    print("🔍 测试连接...")
    if await crawler.test_connection():
        print("✅ 连接测试成功")
        
        # 显示可用主题
        themes = crawler.get_available_themes()
        print(f"📋 可用主题: {len(themes)} 个")
        for fid, theme in themes.items():
            print(f"  - {fid}: {theme['name']}")
        
        # 爬取亚洲无码前2页
        print("🕷️ 开始爬取测试...")
        threads = await crawler.crawl_single_theme(
            fid="36",
            start_page=1,
            end_page=2,
            keywords=["中文字幕", "无码"]
        )
        
        print(f"✅ 爬取完成，共 {len(threads)} 个帖子")
        
        # 显示前5个结果
        print("📝 前5个结果:")
        for i, thread in enumerate(threads[:5]):
            print(f"  {i+1}. {thread['title']} (TID: {thread['tid']})")
    else:
        print("❌ 连接测试失败")

if __name__ == "__main__":
    asyncio.run(test_new_crawler())
