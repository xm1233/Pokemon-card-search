"""本机卡查接口。启动：uvicorn app.main:app --host 127.0.0.1 --port 8000。页面由 frontend 的 Vue 开发服务提供。"""

import json
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.match import SUGGESTION_LIMIT, species_by_prefix
from app.tcgdex_catalog import TcgdexCatalog, TcgdexError

logging.basicConfig(level=logging.INFO)

ROOT = Path(__file__).resolve().parents[1]
SPECIES_PATH = ROOT / "data" / "species.json"

species = json.loads(SPECIES_PATH.read_text(encoding="utf-8"))
catalog = TcgdexCatalog(species)

app = FastAPI(title="Pokemon-card-search")


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
def cards(en: str, page: int = 1):
    """按字典中的英文名，用 TCGdex 查英文国际版卡并分页返回。"""
    if en not in catalog.english_names:
        raise HTTPException(status_code=400, detail="请从候选列表里选择一只宝可梦")
    try:
        return catalog.cards_page(en, page)
    except TcgdexError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/cards/{card_id}")
def card_detail(card_id: str):
    """单张卡详情。card_id 为 TCGdex id，例如 swsh3-136。"""
    try:
        detail = catalog.card_detail(card_id)
    except TcgdexError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if detail is None:
        raise HTTPException(status_code=404, detail="找不到这张卡")
    return detail
