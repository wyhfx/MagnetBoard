#!/bin/bash

# 配置代理环境变量
export HTTP_PROXY=${HTTP_PROXY:-http://127.0.0.1:7890}
export HTTPS_PROXY=${HTTPS_PROXY:-http://127.0.0.1:7890}
export http_proxy=${http_proxy:-http://127.0.0.1:7890}
export https_proxy=${https_proxy:-http://127.0.0.1:7890}
export NO_PROXY=${NO_PROXY:-localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12}

# 为pip配置代理（开发环境不需要apt代理）
if [ ! -z "$HTTP_PROXY" ]; then
    echo "配置pip代理: $HTTP_PROXY"
    
    # 配置pip代理
    mkdir -p ~/.pip
    echo "[global]" > ~/.pip/pip.conf
    echo "proxy = $HTTP_PROXY" >> ~/.pip/pip.conf
    echo "https_proxy = $HTTPS_PROXY" >> ~/.pip/pip.conf
fi

# 启动应用
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
