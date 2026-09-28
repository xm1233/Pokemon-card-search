"""读取 TCG API 配置（密钥不入库）。"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def get_tcgapi_key() -> str:
    key = os.getenv("TCGAPI_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "未配置 TCGAPI_KEY。请在项目根目录复制 .env.example 为 .env 并填入密钥。"
        )
    return key
