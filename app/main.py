"""本机卡查服务入口。启动：uvicorn app.main:app --host 127.0.0.1 --port 8000"""

import json
import logging
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.config import get_tcgapi_key
from app.match import SUGGESTION_LIMIT, species_by_prefix
from app.tcg_client import create_tcgapi
from app.tcgapi_catalog import TcgApiCatalog, TcgApiCatalogError
from app.tcgdex_catalog import TcgdexCatalog, TcgdexError

logging.basicConfig(level=logging.INFO)

ROOT = Path(__file__).resolve().parents[1]
SPECIES_PATH = ROOT / "data" / "species.json"
INDEX_PATH = ROOT / "static" / "index.html"

SourceLiteral = Literal["tcgapi", "tcgdex"]

species = json.loads(SPECIES_PATH.read_text(encoding="utf-8"))
tcgapi_catalog = TcgApiCatalog(species, create_tcgapi(get_tcgapi_key()))
tcgdex_catalog = TcgdexCatalog(species)

app = FastAPI(title="Pokemon-card-search")


def _normalize_source(source: str) -> SourceLiteral:
    value = source.strip().lower()
    if value not in ("tcgapi", "tcgdex"):
        raise HTTPException(status_code=400, detail="source 只能是 tcgapi 或 tcgdex")
    return value  # type: ignore[return-value]


@app.get("/")
def index():
    return FileResponse(INDEX_PATH)


@app.get("/api/species")
def suggest(q: str = ""):
    """根据简体名前缀返回物种候选，供前端点选后再查卡。"""
    matches = species_by_prefix(species, q)
    return {
        "query": q.strip(),
        "total": len(matches),
        "items": matches[:SUGGESTION_LIMIT],
    }


@app.get("/api/cards")
def cards(en: str, page: int = 1, source: str = "tcgapi"):
    """按字典中的英文名查卡，分页返回；source 切换 TCG API / TCGdex。"""
    src = _normalize_source(source)
    catalog = tcgapi_catalog if src == "tcgapi" else tcgdex_catalog
    if en not in catalog.english_names:
        raise HTTPException(status_code=400, detail="请从候选列表里选择一只宝可梦")
    try:
        return catalog.cards_page(en, page)
    except TcgApiCatalogError as exc:
        status = 429 if "上限" in str(exc) else 502
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    except TcgdexError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/cards/{card_id}")
def card_detail(card_id: str, source: str = "tcgapi"):
    """单张卡详情；tcgapi 用数字 id，tcgdex 用如 swsh3-136 的 id。"""
    src = _normalize_source(source)
    try:
        if src == "tcgapi":
            try:
                numeric_id = int(card_id)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="TCG API 卡 id 应为数字") from exc
            detail = tcgapi_catalog.card_detail(numeric_id)
        else:
            detail = tcgdex_catalog.card_detail(card_id)
    except TcgApiCatalogError as exc:
        status = 429 if "上限" in str(exc) else 502
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    except TcgdexError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if detail is None:
        raise HTTPException(status_code=404, detail="找不到这张卡")
    return detail
