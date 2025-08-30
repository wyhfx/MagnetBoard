#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载器管理器
支持qBittorrent下载器，包含完善的代理设置
"""

import requests
import json
import logging
from typing import Dict, Union, Optional, List
from urllib.parse import urlparse, urljoin
import ipaddress
from settings_manager import SettingsManager

logger = logging.getLogger(__name__)

class DownloaderManager:
    def __init__(self, db_session=None):
        """初始化下载器管理器"""
        from db import SessionLocal
        if db_session is None:
            from sqlalchemy.orm import sessionmaker
            from db import engine
            Session = sessionmaker(bind=engine)
            db_session = Session()
        
        self.db_session = db_session
        self.settings_manager = SettingsManager(db_session)
        self.session = requests.Session()
        self._setup_session()
    
    def _is_lan_address(self, host: str) -> bool:
        """检查是否为局域网地址"""
        try:
            # 解析主机地址
            if ':' in host:
                host = host.split(':')[0]  # 移除端口号
            
            # 检查是否为IP地址
            ip = ipaddress.ip_address(host)
            
            # 检查是否为局域网地址
            return (
                ip.is_private or  # 私有IP地址 (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
                ip.is_loopback or  # 回环地址 (127.0.0.0/8)
                ip.is_link_local or  # 链路本地地址 (169.254.0.0/16)
                ip.is_multicast  # 多播地址
            )
        except ValueError:
            # 如果不是IP地址，检查是否为本地主机名
            local_hostnames = {
                'localhost', '127.0.0.1', '::1',
                'local', 'localdomain', 'localhost.localdomain'
            }
            return host.lower() in local_hostnames
    
    def _should_use_proxy(self, target_url: str) -> bool:
        """判断是否应该使用代理"""
        try:
            parsed = urlparse(target_url)
            host = parsed.hostname
            
            if not host:
                return False
            
            # 检查是否为局域网地址
            if self._is_lan_address(host):
                logger.info(f"目标地址 {host} 为局域网地址，不使用代理")
                return False
            
            # 获取no_proxy设置
            no_proxy = self.get_setting_value('no_proxy', 'localhost,127.0.0.1')
            if no_proxy:
                no_proxy_hosts = [h.strip().lower() for h in no_proxy.split(',')]
                if host.lower() in no_proxy_hosts:
                    logger.info(f"目标地址 {host} 在no_proxy列表中，不使用代理")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"检查代理使用失败: {e}")
            return False
    
    def _setup_session(self):
        """设置会话"""
        # 获取代理设置
        proxy_enabled = self.get_setting_value('proxy_enabled', 'false').lower() == 'true'
        
        if proxy_enabled:
            proxy_host = self.get_setting_value('proxy_host', '')
            proxy_port = self.get_setting_value('proxy_port', '')
            proxy_username = self.get_setting_value('proxy_username', '')
            proxy_password = self.get_setting_value('proxy_password', '')
            
            if proxy_host and proxy_port:
                proxy_url = f"http://{proxy_host}:{proxy_port}"
                if proxy_username and proxy_password:
                    proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"
                
                # 设置代理，但会在请求时动态判断是否使用
                self.proxy_config = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                logger.info(f"代理已配置: {proxy_host}:{proxy_port}")
            else:
                self.proxy_config = None
                logger.warning("代理已启用但配置不完整")
        else:
            self.proxy_config = None
            logger.info("代理功能未启用")
    
    def _get_proxies_for_request(self, target_url: str) -> Optional[Dict[str, str]]:
        """根据目标URL获取代理配置"""
        if not self.proxy_config:
            return None
        
        if self._should_use_proxy(target_url):
            logger.debug(f"对 {target_url} 使用代理")
            return self.proxy_config
        else:
            logger.debug(f"对 {target_url} 不使用代理")
            return None
    
    def get_setting_value(self, key: str, default: str = '') -> str:
        """获取设置值"""
        try:
            # 首先尝试获取通用设置
            setting = self.settings_manager.get_setting(key)
            if setting:
                return setting
            
            # 如果通用设置不存在，尝试获取特定下载器类型的设置
            downloader_type = self.settings_manager.get_setting('downloader_type', 'qbittorrent')
            if downloader_type:
                specific_key = key.replace('downloader_', f'{downloader_type}_')
                specific_setting = self.settings_manager.get_setting(specific_key)
                if specific_setting:
                    return specific_setting
            
            return default
        except Exception as e:
            logger.error(f"获取设置 {key} 失败: {e}")
            return default
    
    def get_downloader_status(self) -> Dict[str, Union[bool, str, Dict]]:
        """获取下载器状态"""
        try:
            enabled_value = self.get_setting_value('downloader_enabled', 'false')
            enabled = enabled_value.lower() == 'true'
            downloader_type = self.get_setting_value('downloader_type', 'qbittorrent')
            
            logger.info(f"下载器状态检查 - enabled_value: {enabled_value}, enabled: {enabled}, type: {downloader_type}")
            
            if not enabled:
                return {
                    "success": False,
                    "message": "下载器功能未启用",
                    "data": {
                        "enabled": False,
                        "downloader_type": downloader_type,
                        "connection": {"success": False, "message": "下载器功能未启用"},
                        "info": {},
                        "config": {}
                    }
                }
            
            # 根据下载器类型测试连接
            if downloader_type == 'qbittorrent':
                connection_result = self._test_qbittorrent_connection()
            elif downloader_type == 'transmission':
                connection_result = self._test_transmission_connection()
            elif downloader_type == 'aria2':
                connection_result = self._test_aria2_connection()
            else:
                connection_result = {"success": False, "message": f"不支持的下载器类型: {downloader_type}"}
            
            # 获取配置信息
            config = self._get_downloader_config()
            
            return {
                "success": True,
                "data": {
                    "enabled": enabled,
                    "downloader_type": downloader_type,
                    "connection": connection_result,
                    "info": connection_result.get("info", {}),
                    "config": config
                }
            }
            
        except Exception as e:
            logger.error(f"获取下载器状态失败: {e}")
            return {
                "success": False,
                "message": f"获取状态失败: {str(e)}",
                "data": {}
            }
    
    def _get_downloader_config(self) -> Dict:
        """获取下载器配置"""
        downloader_type = self.get_setting_value('downloader_type', 'qbittorrent')
        
        if downloader_type == 'qbittorrent':
            return {
                "url": self.get_setting_value('downloader_url', ''),
                "username": self.get_setting_value('downloader_username', ''),
                "password": "***" if self.get_setting_value('downloader_password') else "",
                "category": self.get_setting_value('downloader_category', ''),
                "save_path": self.get_setting_value('downloader_save_path', ''),
                "auto_start": self.get_setting_value('downloader_auto_start', 'true')
            }
        elif downloader_type == 'transmission':
            return {
                "url": self.get_setting_value('downloader_url', ''),
                "username": self.get_setting_value('downloader_username', ''),
                "password": "***" if self.get_setting_value('downloader_password') else "",
                "category": self.get_setting_value('downloader_category', ''),
                "save_path": self.get_setting_value('downloader_save_path', ''),
                "auto_start": self.get_setting_value('downloader_auto_start', 'true')
            }
        elif downloader_type == 'aria2':
            return {
                "url": self.get_setting_value('downloader_url', ''),
                "secret": "***" if self.get_setting_value('downloader_secret') else "",
                "category": self.get_setting_value('downloader_category', ''),
                "save_path": self.get_setting_value('downloader_save_path', ''),
                "auto_start": self.get_setting_value('downloader_auto_start', 'true')
            }
        
        return {}
    
    def _test_qbittorrent_connection(self) -> Dict[str, Union[bool, str]]:
        """测试qBittorrent连接"""
        try:
            url = self.get_setting_value('downloader_url', '')
            username = self.get_setting_value('downloader_username', '')
            password = self.get_setting_value('downloader_password', '')
            
            if not url:
                return {"success": False, "message": "qBittorrent地址未配置"}
            
            # 获取代理配置
            proxies = self._get_proxies_for_request(url)
            
            # 先登录qBittorrent
            login_url = urljoin(url, '/api/v2/auth/login')
            login_data = {
                'username': username,
                'password': password
            }
            
            login_response = self.session.post(login_url, data=login_data, proxies=proxies, timeout=10)
            if login_response.status_code != 200:
                return {"success": False, "message": "qBittorrent登录失败，请检查用户名和密码"}
            
            # 获取qBittorrent版本信息
            version_url = urljoin(url, '/api/v2/app/version')
            response = self.session.get(version_url, proxies=proxies, timeout=10)
            
            if response.status_code == 200:
                version = response.text.strip()
                return {
                    "success": True, 
                    "message": f"qBittorrent连接成功，版本: {version}",
                    "info": {"version": version}
                }
            else:
                return {"success": False, "message": f"获取版本信息失败: {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "无法连接到qBittorrent，请检查地址和端口"}
        except requests.exceptions.Timeout:
            return {"success": False, "message": "连接超时，请检查网络"}
        except Exception as e:
            return {"success": False, "message": f"连接测试失败: {str(e)}"}

    def _test_transmission_connection(self) -> Dict[str, Union[bool, str]]:
        """测试Transmission连接"""
        try:
            url = self.get_setting_value('downloader_url', '')
            username = self.get_setting_value('downloader_username', '')
            password = self.get_setting_value('downloader_password', '')
            
            if not url:
                return {"success": False, "message": "Transmission地址未配置"}
            
            # 确保URL以/transmission/rpc结尾
            if not url.endswith('/transmission/rpc'):
                if url.endswith('/'):
                    url = url + 'transmission/rpc'
                else:
                    url = url + '/transmission/rpc'
            
            # 获取代理配置
            proxies = self._get_proxies_for_request(url)
            
            # 设置认证信息
            auth = None
            if username and password:
                auth = (username, password)
            
            # 获取Transmission会话ID
            session_response = self.session.get(url, proxies=proxies, auth=auth, timeout=10)
            
            # 检查是否需要认证
            if session_response.status_code == 401:
                return {"success": False, "message": "Transmission需要认证，请检查用户名和密码"}
            
            session_id = session_response.headers.get('X-Transmission-Session-Id', '')
            
            if not session_id:
                # 如果没有会话ID，尝试直接发送请求
                test_data = {
                    "method": "session-get",
                    "arguments": {},
                    "tag": 1
                }
                
                response = self.session.post(url, json=test_data, proxies=proxies, auth=auth, timeout=10)
                
                if response.status_code == 409:  # 冲突，需要会话ID
                    session_id = response.headers.get('X-Transmission-Session-Id', '')
                    if not session_id:
                        return {"success": False, "message": "无法获取Transmission会话ID，请检查RPC配置"}
                
                # 设置会话ID用于后续请求
                if session_id:
                    self.session.headers.update({'X-Transmission-Session-Id': session_id})
                
                # 重新发送请求
                response = self.session.post(url, json=test_data, proxies=proxies, auth=auth, timeout=10)
            else:
                # 设置会话ID用于后续请求
                self.session.headers.update({'X-Transmission-Session-Id': session_id})
                
                # 测试连接并获取版本信息
                test_data = {
                    "method": "session-get",
                    "arguments": {},
                    "tag": 1
                }
                
                response = self.session.post(url, json=test_data, proxies=proxies, auth=auth, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result') == 'success':
                    version = result.get('arguments', {}).get('version', 'unknown')
                    return {
                        "success": True,
                        "message": f"Transmission连接成功，版本: {version}",
                        "info": {"version": version}
                    }
                else:
                    return {"success": False, "message": f"Transmission响应错误: {result.get('result', 'unknown')}"}
            else:
                return {"success": False, "message": f"Transmission连接失败: {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "无法连接到Transmission，请检查地址和端口"}
        except requests.exceptions.Timeout:
            return {"success": False, "message": "连接超时，请检查网络"}
        except Exception as e:
            return {"success": False, "message": f"Transmission连接测试失败: {str(e)}"}

    def _test_aria2_connection(self) -> Dict[str, Union[bool, str]]:
        """测试Aria2连接"""
        try:
            url = self.get_setting_value('downloader_url', '')
            secret = self.get_setting_value('downloader_secret', '')
            
            if not url:
                return {"success": False, "message": "Aria2地址未配置"}
            
            # 获取代理配置
            proxies = self._get_proxies_for_request(url)
            
            # 构建请求数据
            test_data = {
                "jsonrpc": "2.0",
                "id": "test",
                "method": "aria2.getVersion",
                "params": []
            }
            
            # 如果有密钥，添加到参数中
            if secret:
                test_data["params"] = [f"token:{secret}"]
            
            response = self.session.post(url, json=test_data, proxies=proxies, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    version = result['result'].get('version', 'unknown')
                    return {
                        "success": True,
                        "message": f"Aria2连接成功，版本: {version}",
                        "info": {"version": version}
                    }
                else:
                    return {"success": False, "message": f"Aria2响应错误: {result.get('error', 'unknown')}"}
            else:
                return {"success": False, "message": f"Aria2连接失败: {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "无法连接到Aria2，请检查地址和端口"}
        except requests.exceptions.Timeout:
            return {"success": False, "message": "连接超时，请检查网络"}
        except Exception as e:
            return {"success": False, "message": f"Aria2连接测试失败: {str(e)}"}
    
    def push_magnet(self, magnet_url: str, title: str = '', tags: List[str] = None) -> Dict[str, Union[bool, str]]:
        """推送磁力链接到下载器"""
        try:
            downloader_type = self.get_setting_value('downloader_type', 'qbittorrent')
            
            if downloader_type == 'qbittorrent':
                return self._push_to_qbittorrent(magnet_url, title, tags or [])
            elif downloader_type == 'transmission':
                return self._push_to_transmission(magnet_url, title, tags or [])
            elif downloader_type == 'aria2':
                return self._push_to_aria2(magnet_url, title, tags or [])
            else:
                return {"success": False, "message": f"不支持的下载器类型: {downloader_type}"}
                
        except Exception as e:
            logger.error(f"推送磁力链接失败: {e}")
            return {"success": False, "message": f"推送失败: {str(e)}"}
    
    def _push_to_qbittorrent(self, magnet_url: str, title: str, tags: List[str]) -> Dict[str, Union[bool, str]]:
        """推送到qBittorrent"""
        try:
            url = self.get_setting_value('downloader_url', '')
            username = self.get_setting_value('downloader_username', '')
            password = self.get_setting_value('downloader_password', '')
            category = self.get_setting_value('downloader_category', '')
            save_path = self.get_setting_value('downloader_save_path', '')
            auto_start = self.get_setting_value('downloader_auto_start', 'true').lower() == 'true'
            
            # 获取代理配置
            proxies = self._get_proxies_for_request(url)
            
            # 登录
            login_url = urljoin(url, '/api/v2/auth/login')
            login_data = {
                'username': username,
                'password': password
            }
            
            login_response = self.session.post(login_url, data=login_data, proxies=proxies, timeout=10)
            if login_response.status_code != 200:
                return {"success": False, "message": "qBittorrent登录失败"}
            
            # 添加磁力链接
            add_url = urljoin(url, '/api/v2/torrents/add')
            add_data = {
                'urls': magnet_url,
                'autoTMM': False,
                'category': category,
                'savepath': save_path,
                'start': 'true' if auto_start else 'false'
            }
            
            response = self.session.post(add_url, data=add_data, proxies=proxies, timeout=10)
            
            if response.status_code == 200:
                return {"success": True, "message": f"成功推送到qBittorrent: {title}"}
            else:
                return {"success": False, "message": f"推送失败: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"推送到qBittorrent失败: {str(e)}"}

    def _push_to_transmission(self, magnet_url: str, title: str, tags: List[str]) -> Dict[str, Union[bool, str]]:
        """推送到Transmission"""
        try:
            url = self.get_setting_value('downloader_url', '')
            username = self.get_setting_value('downloader_username', '')
            password = self.get_setting_value('downloader_password', '')
            category = self.get_setting_value('downloader_category', '')
            save_path = self.get_setting_value('downloader_save_path', '')
            auto_start = self.get_setting_value('downloader_auto_start', 'true').lower() == 'true'
            
            # 确保URL以/transmission/rpc结尾
            if not url.endswith('/transmission/rpc'):
                if url.endswith('/'):
                    url = url + 'transmission/rpc'
                else:
                    url = url + '/transmission/rpc'
            
            # 获取代理配置
            proxies = self._get_proxies_for_request(url)
            
            # 设置认证信息
            auth = None
            if username and password:
                auth = (username, password)
            
            # 获取会话ID
            session_response = self.session.get(url, proxies=proxies, auth=auth, timeout=10)
            session_id = session_response.headers.get('X-Transmission-Session-Id', '')
            
            if not session_id:
                # 尝试直接发送请求获取会话ID
                test_data = {
                    "method": "session-get",
                    "arguments": {},
                    "tag": 1
                }
                
                response = self.session.post(url, json=test_data, proxies=proxies, auth=auth, timeout=10)
                
                if response.status_code == 409:  # 冲突，需要会话ID
                    session_id = response.headers.get('X-Transmission-Session-Id', '')
                    if not session_id:
                        return {"success": False, "message": "无法获取Transmission会话ID"}
                
                # 设置会话ID
                if session_id:
                    self.session.headers.update({'X-Transmission-Session-Id': session_id})
            else:
                # 设置会话ID
                self.session.headers.update({'X-Transmission-Session-Id': session_id})
            
            # 添加磁力链接
            add_data = {
                "method": "torrent-add",
                "arguments": {
                    "filename": magnet_url,
                    "download-dir": save_path,
                    "paused": not auto_start
                },
                "tag": 1
            }
            
            # 如果有分类，添加到标签中
            if category:
                add_data["arguments"]["labels"] = [category] + tags
            
            response = self.session.post(url, json=add_data, proxies=proxies, auth=auth, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result') == 'success':
                    return {"success": True, "message": f"成功推送到Transmission: {title}"}
                else:
                    return {"success": False, "message": f"Transmission添加失败: {result.get('result', 'unknown')}"}
            else:
                return {"success": False, "message": f"推送失败: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"推送到Transmission失败: {str(e)}"}

    def _push_to_aria2(self, magnet_url: str, title: str, tags: List[str]) -> Dict[str, Union[bool, str]]:
        """推送到Aria2"""
        try:
            url = self.get_setting_value('downloader_url', '')
            secret = self.get_setting_value('downloader_secret', '')
            category = self.get_setting_value('downloader_category', '')
            save_path = self.get_setting_value('downloader_save_path', '')
            auto_start = self.get_setting_value('downloader_auto_start', 'true').lower() == 'true'
            
            # 获取代理配置
            proxies = self._get_proxies_for_request(url)
            
            # 构建请求数据
            add_data = {
                "jsonrpc": "2.0",
                "id": "add",
                "method": "aria2.addUri",
                "params": [
                    [magnet_url],
                    {
                        "dir": save_path,
                        "pause": not auto_start
                    }
                ]
            }
            
            # 如果有密钥，添加到参数中
            if secret:
                add_data["params"][1]["rpc-secret"] = secret
            
            # 如果有分类，添加到注释中
            if category or tags:
                comment = f"Category: {category}, Tags: {', '.join(tags)}" if category and tags else f"Category: {category}" if category else f"Tags: {', '.join(tags)}"
                add_data["params"][1]["comment"] = comment
            
            response = self.session.post(url, json=add_data, proxies=proxies, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    return {"success": True, "message": f"成功推送到Aria2: {title}"}
                else:
                    return {"success": False, "message": f"Aria2添加失败: {result.get('error', 'unknown')}"}
            else:
                return {"success": False, "message": f"推送失败: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"推送到Aria2失败: {str(e)}"}
    
    def push_batch_magnets(self, magnet_urls: List[str], title_prefix: str = '', tags: List[str] = None) -> Dict[str, Union[bool, str, Dict]]:
        """批量推送磁力链接"""
        try:
            results = []
            success_count = 0
            failed_count = 0
            
            for i, magnet_url in enumerate(magnet_urls):
                title = f"{title_prefix}_{i+1}" if title_prefix else f"磁力链接_{i+1}"
                result = self.push_magnet(magnet_url, title, tags or [])
                results.append(result)
                
                if result.get('success'):
                    success_count += 1
                else:
                    failed_count += 1
            
            return {
                "success": True,
                "message": f"批量推送完成: 成功 {success_count} 个，失败 {failed_count} 个",
                "data": {
                    "total": len(magnet_urls),
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "results": results
                }
            }
            
        except Exception as e:
            logger.error(f"批量推送失败: {e}")
            return {"success": False, "message": f"批量推送失败: {str(e)}"}

    def test_connection(self) -> Dict[str, Union[bool, str]]:
        """测试当前配置的下载器连接"""
        try:
            downloader_type = self.get_setting_value('downloader_type', 'qbittorrent')
            
            if downloader_type == 'qbittorrent':
                return self._test_qbittorrent_connection()
            elif downloader_type == 'transmission':
                return self._test_transmission_connection()
            elif downloader_type == 'aria2':
                return self._test_aria2_connection()
            else:
                return {"success": False, "message": f"不支持的下载器类型: {downloader_type}"}
                
        except Exception as e:
            logger.error(f"测试连接失败: {e}")
            return {"success": False, "message": f"测试连接失败: {str(e)}"}

class DownloaderFactory:
    @staticmethod
    def create_downloader(settings: Dict = None) -> DownloaderManager:
        return DownloaderManagerit 