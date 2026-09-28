"""创建 TCG API 客户端（直连，不读系统代理）。"""

import httpx
from tcgapi import TCGApi


def create_tcgapi(api_key: str) -> TCGApi:
    """Windows 上若配置了 Clash 等但未启动，httpx 默认 trust_env 会连不上 api.tcgapi.dev。"""
    http = httpx.Client(timeout=60.0, trust_env=False)
    return TCGApi(api_key=api_key, client=http)
