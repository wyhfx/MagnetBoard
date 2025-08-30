#!/usr/bin/env python3
"""
文件监控自动构建脚本
监控前端文件变化，自动重新构建
"""
import os
import time
import subprocess
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FrontendBuildHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_build_time = 0
        self.build_cooldown = 5  # 5秒冷却时间，避免频繁构建
        self.is_building = False
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # 只监控前端源代码文件
        if not event.src_path.endswith(('.tsx', '.ts', '.js', '.jsx', '.css', '.scss')):
            return
            
        # 跳过node_modules和build目录
        if 'node_modules' in event.src_path or 'build' in event.src_path:
            return
            
        current_time = time.time()
        if current_time - self.last_build_time < self.build_cooldown:
            return
            
        if self.is_building:
            return
            
        print(f"🔄 检测到文件变化: {event.src_path}")
        self.trigger_build()
        
    def trigger_build(self):
        if self.is_building:
            return
            
        self.is_building = True
        self.last_build_time = time.time()
        
        # 在后台线程中执行构建
        thread = threading.Thread(target=self.build_frontend)
        thread.daemon = True
        thread.start()
        
    def build_frontend(self):
        try:
            print("🔨 开始自动构建前端...")
            
            # 切换到前端目录
            frontend_dir = Path("frontend")
            if not frontend_dir.exists():
                print("❌ 前端目录不存在")
                return
                
            # 执行构建命令
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=frontend_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ 前端自动构建完成！")
            else:
                print(f"❌ 构建失败: {result.stderr}")
                
        except Exception as e:
            print(f"❌ 构建过程中出错: {e}")
        finally:
            self.is_building = False

def main():
    print("🚀 启动前端文件监控...")
    print("📁 监控目录: frontend/src")
    print("💡 修改前端文件后将自动重新构建")
    print("⏹️  按 Ctrl+C 停止监控")
    print("-" * 50)
    
    # 检查前端目录
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ 前端目录不存在，请确保在项目根目录运行")
        return
        
    # 检查package.json
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print("❌ package.json不存在，请先安装前端依赖")
        return
        
    # 创建事件处理器和观察者
    event_handler = FrontendBuildHandler()
    observer = Observer()
    observer.schedule(event_handler, str(frontend_dir / "src"), recursive=True)
    
    try:
        observer.start()
        print("✅ 文件监控已启动")
        
        # 保持运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  停止文件监控...")
        observer.stop()
        
    observer.join()
    print("👋 文件监控已停止")

if __name__ == "__main__":
    main()
