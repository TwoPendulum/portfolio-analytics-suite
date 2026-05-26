import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import numpy as np

from core.optimizer import (
    build_cov_matrix,
    efficient_frontier,
    compute_asset_points,
    compute_historical_mu_sigma,
)

router = APIRouter()


class FrontierRequest(BaseModel):
    tickers: List[str]
    mu: List[float]
    sigma: List[float]
    monthlyRhoMatrix: List[List[float]]
    rf: float = 0.045
    allowShort: bool = False
    nPoints: int = 100


@router.post("/api/frontier")
async def frontier(req: FrontierRequest):
    mu = np.array(req.mu)
    sigma = np.array(req.sigma)
    rho_matrix = np.array(req.monthlyRhoMatrix)
    rf = req.rf

    Sigma = build_cov_matrix(sigma, rho_matrix)

    ef_points, ms_pt, mv_pt, warnings = efficient_frontier(
        mu, Sigma, rf, req.allowShort, n_points=req.nPoints,
    )

    asset_pts = compute_asset_points(mu, np.sqrt(np.diag(Sigma)), req.tickers)

    def serialize_pt(pt):
        if pt is None:
            return None
        return {
            "weights": pt["weights"].tolist(),
            "ret": float(pt["ret"]),
            "vol": float(pt["vol"]),
            "sharpe": float(pt["sharpe"]),
        }

    return {
        "efPoints": [serialize_pt(p) for p in ef_points],
        "maxSharpe": serialize_pt(ms_pt),
        "minVol": serialize_pt(mv_pt),
        "assetPoints": {
            "tickers": asset_pts["ticker"].tolist(),
            "vol": asset_pts["vol"].tolist(),
            "ret": asset_pts["ret"].tolist(),
        },
        "warnings": warnings,
    }
