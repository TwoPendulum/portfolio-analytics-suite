import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter
from core.data_loader import load_asset_config

router = APIRouter()


@router.get("/api/assets")
async def get_assets():
    assets = load_asset_config()
    return {"assets": assets}


@router.get("/api/methodology/{lang}")
async def get_methodology(lang: str):
    doc_path = Path(__file__).parent.parent.parent / "docs" / f"methodology_{lang}.md"
    if not doc_path.exists():
        return {"content": "", "error": f"Documentation not found for language: {lang}"}
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"content": content}
