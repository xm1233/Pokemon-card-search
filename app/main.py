"""Local card search. Run: uvicorn app.main:app --host 127.0.0.1 --port 8000"""

import json
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.cards import Catalog, TcgdexError
from app.match import SUGGESTION_LIMIT, species_by_prefix

logging.basicConfig(level=logging.INFO)

ROOT = Path(__file__).resolve().parents[1]
SPECIES_PATH = ROOT / "data" / "species.json"
INDEX_PATH = ROOT / "static" / "index.html"

species = json.loads(SPECIES_PATH.read_text(encoding="utf-8"))
catalog = Catalog(species)

app = FastAPI(title="宝可梦卡查")


@app.get("/")
def index():
    return FileResponse(INDEX_PATH)


@app.get("/api/species")
def suggest(q: str = ""):
    matches = species_by_prefix(species, q)
    return {
        "query": q.strip(),
        "total": len(matches),
        "items": matches[:SUGGESTION_LIMIT],
    }


@app.get("/api/cards")
def cards(en: str, page: int = 1):
    if en not in catalog.english_names:
        raise HTTPException(status_code=400, detail="请从候选列表里选择一只宝可梦")
    try:
        return catalog.cards_page(en, page)
    except TcgdexError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/cards/{card_id}")
def card_detail(card_id: str):
    try:
        detail = catalog.card_detail(card_id)
    except TcgdexError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if detail is None:
        raise HTTPException(status_code=404, detail="找不到这张卡")
    return detail
