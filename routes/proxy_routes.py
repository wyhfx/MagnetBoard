# routes/proxy_routes.py
import json
import requests
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

DATA_FILE = Path("data/proxies.json")
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

router = APIRouter()

class ProxyItem(BaseModel):
    id: str
    name: str
    proxy_url: str  # 允许 http/https/socks5
    enabled: bool = True
    note: Optional[str] = None

class ProxyUpdate(BaseModel):
    name: str
    proxy_url: str
    enabled: bool = True
    note: Optional[str] = None

class ProxyTestRequest(BaseModel):
    proxy_url: str

def load_all() -> List[ProxyItem]:
    if DATA_FILE.exists():
        return [ProxyItem(**x) for x in json.loads(DATA_FILE.read_text("utf-8"))]
    return []

def save_all(items: List[ProxyItem]):
    DATA_FILE.write_text(json.dumps([x.model_dump() for x in items], ensure_ascii=False, indent=2), "utf-8")

@router.post("/api/proxy/test")
def test_proxy(request: ProxyTestRequest):
    """测试代理连接"""
    try:
        # 配置代理
        proxies = {
            'http': request.proxy_url,
            'https': request.proxy_url
        }
        
        # 测试连接（使用一个简单的测试网站）
        response = requests.get(
            'http://httpbin.org/ip',
            proxies=proxies,
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "代理连接测试成功",
                "data": {
                    "ip": response.json().get("origin", "未知"),
                    "proxy_url": request.proxy_url
                }
            }
        else:
            return {
                "success": False,
                "message": f"代理连接测试失败，状态码: {response.status_code}"
            }
            
    except requests.exceptions.ProxyError:
        return {
            "success": False,
            "message": "代理连接失败，请检查代理地址是否正确"
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "代理连接超时，请检查网络连接"
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "无法连接到代理服务器"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"代理测试失败: {str(e)}"
        }

@router.get("/api/proxies")
def list_proxies():
    return {"success": True, "data": [x.model_dump() for x in load_all()]}

@router.post("/api/proxies")
def create_proxy(item: ProxyItem):
    items = load_all()
    if any(x.id == item.id for x in items):
        raise HTTPException(status_code=400, detail="ID 已存在")
    items.append(item)
    save_all(items)
    return {"success": True, "data": item.model_dump()}

@router.put("/api/proxies/{pid}")
def update_proxy(pid: str, item: ProxyUpdate):
    items = load_all()
    for i, x in enumerate(items):
        if x.id == pid:
            # 更新字段，保持原有id
            updated_item = ProxyItem(
                id=pid,
                name=item.name,
                proxy_url=item.proxy_url,
                enabled=item.enabled,
                note=item.note
            )
            items[i] = updated_item
            save_all(items)
            return {"success": True, "data": updated_item.model_dump()}
    raise HTTPException(status_code=404, detail="未找到该代理")

@router.delete("/api/proxies/{pid}")
def delete_proxy(pid: str):
    items = load_all()
    n = len(items)
    items = [x for x in items if x.id != pid]
    if len(items) == n:
        raise HTTPException(status_code=404, detail="未找到该代理")
    save_all(items)
    return {"success": True, "data": True}
