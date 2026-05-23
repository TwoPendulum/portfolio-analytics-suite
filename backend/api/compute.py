import sys, os
from pathlib import Path

# Add parent to path so we can import core/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from core.data_loader import fetch_data, load_asset_config
from core.correlation import compute_correlation_pipeline
from core.optimizer import compute_historical_mu_sigma

router = APIRouter()


class ComputeRequest(BaseModel):
    tickers: List[str]
    startDate: str
    endDate: str
    Q: float = 0.001
    R: float = 0.5


@router.post("/api/compute")
async def compute(req: ComputeRequest):
    returns, data_warnings = fetch_data(req.tickers, req.startDate, req.endDate)
    warnings = list(data_warnings)

    matrices, rho_series, obs_by_freq, corr_warnings = compute_correlation_pipeline(
        returns, Q=req.Q, R=req.R
    )
    warnings.extend(corr_warnings)

    # Serialize matrices
    serialized_matrices: Dict[str, Dict[str, Any]] = {}
    for freq, mat in matrices.items():
        serialized_matrices[freq] = {
            "tickers": list(mat.index),
            "values": mat.values.tolist(),
        }

    # Serialize rho_series: include dates + values, store (i,j) once with i < j
    serialized_rho: Dict[str, Dict[str, dict]] = {}
    serialized_obs: Dict[str, Dict[str, dict]] = {}
    for freq, pair_dict in rho_series.items():
        serialized_rho[freq] = {}
        serialized_obs[freq] = {}
        seen = set()
        for (i, j), series in pair_dict.items():
            key = f"{i}|{j}" if i < j else f"{j}|{i}"
            if key in seen:
                continue
            seen.add(key)
            serialized_rho[freq][key] = {
                "dates": [str(d)[:10] for d in series.index],
                "values": series.tolist(),
            }
        # Serialize obs for the same pairs
        obs_dict = obs_by_freq.get(freq, {})
        for (i, j), obs_series in obs_dict.items():
            key = f"{i}|{j}" if i < j else f"{j}|{i}"
            if key in serialized_obs[freq]:
                continue
            serialized_obs[freq][key] = {
                "dates": [str(d)[:10] for d in obs_series.index],
                "values": obs_series.tolist(),
            }

    # Historical estimates for auto-fill
    tickers_list = list(returns.columns)
    ann_mu, ann_sigma = compute_historical_mu_sigma(returns, tickers_list)
    historical = {
        t: {"mu": round(float(ann_mu.get(t, 0)) * 100, 2), "sigma": round(float(ann_sigma.get(t, 0)) * 100, 2)}
        for t in tickers_list
    }

    return {
        "latestMatrices": serialized_matrices,
        "rhoSeries": serialized_rho,
        "obsSeries": serialized_obs,
        "activeTickers": tickers_list,
        "warnings": warnings,
        "historical": historical,
    }
