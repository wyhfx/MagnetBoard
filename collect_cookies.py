#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Playwright收集cookies
"""

import asyncio
import json
import os
from playwright.async_api import async_playwright

async def collect_cookies(target_url: str = "https://sehuatang.org", headless: bool = False):
    """收集cookies"""
    print("🚀 开始收集cookies...")
    
    # 获取代理配置
    proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    if proxy:
        print(f"🔗 使用代理: {proxy}")
        # 在Docker环境中，将host.docker.internal替换为实际的IP地址
        if 'host.docker.internal' in proxy:
            proxy = proxy.replace('host.docker.internal', '192.168.31.85')
            print(f"🔗 修正代理地址: {proxy}")
    
    async with async_playwright() as p:
        # 配置浏览器启动参数
        browser_args = []
        if proxy:
            browser_args.extend([
                f'--proxy-server={proxy}',
                '--ignore-certificate-errors',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ])
        
        # 在Docker环境中强制使用headless模式
        is_docker = os.path.exists('/.dockerenv')
        if is_docker:
            headless = True
            print("🐳 检测到Docker环境，强制使用headless模式")
        
        browser = await p.chromium.launch(
            headless=headless,
            args=browser_args
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print(f"📡 访问目标网站: {target_url}")
            await page.goto(target_url, wait_until="networkidle", timeout=30000)
            
            # 等待页面加载
            await page.wait_for_timeout(3000)
            
            # 检查是否在Cloudflare页面
            title = await page.title()
            print(f"📄 页面标题: {title}")
            
            if "阿尔贝·加缪" in title or "约翰·洛克" in title:
                print("🛡️ 检测到Cloudflare保护页面，等待验证...")
                
                # 等待Cloudflare验证完成
                await page.wait_for_timeout(10000)
                
                # 再次检查页面标题
                title = await page.title()
                print(f"📄 验证后页面标题: {title}")
                
                # 如果还是保护页面，等待更长时间
                if "阿尔贝·加缪" in title or "约翰·洛克" in title:
                    print("⏳ 继续等待Cloudflare验证...")
                    await page.wait_for_timeout(15000)
                    title = await page.title()
                    print(f"📄 最终页面标题: {title}")
            
            # 处理18+同意按钮
            print("🔍 查找18+同意按钮...")
            selectors = [
                "button:has-text('同意')", 
                "button:has-text('进入')",
                "button:has-text('18+')",
                "a:has-text('同意')",
                "a:has-text('进入')"
            ]
            
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    print(f"✅ 找到按钮: {selector}")
                    await page.click(selector)
                    print("✅ 点击成功")
                    break
                except:
                    continue
            
            # 等待页面加载
            await page.wait_for_timeout(5000)
            
            # 最终检查页面标题
            final_title = await page.title()
            print(f"📄 最终页面标题: {final_title}")
            
            # 获取cookies
            cookies = await context.cookies()
            print(f"🍪 收集到 {len(cookies)} 个cookies")
            
            # 保存cookies
            os.makedirs("data", exist_ok=True)
            with open("data/cookies.json", 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            print("✅ cookies已保存到 data/cookies.json")
            
            # 如果不是headless模式，等待用户确认
            if not headless:
                input("按回车键关闭浏览器...")
            
            return cookies
            
        except Exception as e:
            print(f"❌ 收集cookies失败: {e}")
            return []
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(collect_cookies(headless=False))
