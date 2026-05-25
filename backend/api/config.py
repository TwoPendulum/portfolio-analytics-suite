import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import yaml
from fastapi import APIRouter
from pydantic import BaseModel
from core.data_loader import load_asset_config

router = APIRouter()


class AddAssetRequest(BaseModel):
    ticker: str
    name: str
    group: str = "Custom"


class UpdateAssetRequest(BaseModel):
    name: str | None = None
    group: str | None = None


@router.get("/api/assets")
async def get_assets():
    assets = load_asset_config()
    return {"assets": assets}


@router.post("/api/assets")
async def add_asset(req: AddAssetRequest):
    config_path = Path(__file__).parent.parent.parent / "config" / "assets.yaml"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {"assets": []}
    except FileNotFoundError:
        config = {"assets": []}

    existing = [a for a in config["assets"] if a["ticker"] == req.ticker]
    if existing:
        return {"assets": config["assets"], "warning": f"{req.ticker} already exists"}

    config["assets"].append({
        "ticker": req.ticker,
        "name": req.name,
        "group": req.group,
    })

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    return {"assets": config["assets"]}


@router.put("/api/assets/{ticker}")
async def update_asset(ticker: str, req: UpdateAssetRequest):
    config_path = Path(__file__).parent.parent.parent / "config" / "assets.yaml"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {"assets": []}
    except FileNotFoundError:
        return {"assets": [], "error": "Config file not found"}

    for asset in config["assets"]:
        if asset["ticker"] == ticker:
            if req.name is not None:
                asset["name"] = req.name
            if req.group is not None:
                asset["group"] = req.group
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            return {"assets": config["assets"]}

    return {"assets": config["assets"], "error": f"Asset {ticker} not found"}


@router.get("/api/methodology/{lang}")
async def get_methodology(lang: str):
    doc_path = Path(__file__).parent.parent.parent / "docs" / f"methodology_{lang}.md"
    if not doc_path.exists():
        return {"content": "", "error": f"Documentation not found for language: {lang}"}
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"content": content}
