#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的115扫码登录脚本
"""

from p115client import P115Client
from pathlib import Path

def main():
    print("🚀 115扫码登录工具")
    print("=" * 50)
    
    # 创建客户端
    client = P115Client()
    
    print("📱 请使用115手机APP扫描上面的二维码登录...")
    print("⚠️  扫码完成后，Cookie会自动保存到115-cookies.txt文件")
    
    try:
        # 等待用户扫码登录
        # 这里会自动显示二维码并等待扫码
        print("✅ 登录成功！")
        
        # 保存Cookie到文件
        cookie_file = "115-cookies.txt"
        
        # 将BaseCookie对象转换为字符串
        if hasattr(client, 'cookies'):
            # 如果是BaseCookie对象，转换为字符串
            if hasattr(client.cookies, 'get_dict'):
                # 转换为字典格式
                cookie_dict = client.cookies.get_dict()
                cookie_string = '; '.join([f"{k}={v}" for k, v in cookie_dict.items()])
            else:
                # 直接转换为字符串
                cookie_string = str(client.cookies)
        else:
            cookie_string = ""
        
        with open(cookie_file, 'w', encoding='utf-8') as f:
            f.write(cookie_string)
        
        print(f"✅ Cookie已保存到: {cookie_file}")
        print(f"Cookie内容: {cookie_string[:100]}...")  # 只显示前100个字符
        
        print("\n📝 使用说明:")
        print("1. 在下载器设置中选择'115离线下载'")
        print("2. 在'115 Cookie文件路径'中输入: 115-cookies.txt")
        print("3. 保存设置并测试连接")
        print("4. 连接成功后即可推送磁力链接到115离线下载")
        
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        print("\n💡 提示:")
        print("- 确保网络连接正常")
        print("- 确保115手机APP已安装并登录")
        print("- 扫码时请确保二维码清晰可见")

if __name__ == "__main__":
    main()
