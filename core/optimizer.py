from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, minimize


def build_cov_matrix(
    sigma: np.ndarray,
    rho_matrix: np.ndarray,
    reg_lambda: float = 1e-6,
) -> np.ndarray:
    """Construct covariance matrix from correlations and volatilities.

    Uses proportional regularization (λ * diag(σ²)) instead of constant (λ * I)
    so that low-volatility assets are not disproportionately inflated when
    the correlation matrix is near-singular (e.g. ρ ≈ 1 between two assets).
    """
    rho = np.clip(rho_matrix, -0.999, 0.999)
    np.fill_diagonal(rho, 1.0)
    Sigma = np.diag(sigma) @ rho @ np.diag(sigma)
    D2 = np.diag(sigma ** 2)
    while True:
        Sigma_reg = Sigma + reg_lambda * D2
        try:
            eigvals = np.linalg.eigvals(Sigma_reg)
            if np.all(eigvals > 0):
                return Sigma_reg
        except np.linalg.LinAlgError:
            pass
        reg_lambda *= 2
        if reg_lambda > 1e-1:
            return Sigma_reg


def max_sharpe(
    mu: np.ndarray,
    Sigma: np.ndarray,
    rf: float,
    allow_short: bool,
) -> Optional[Dict]:
    """Find the maximum Sharpe ratio portfolio."""
    n = len(mu)

    def _neg_sharpe(w):
        ret = w @ mu
        vol = np.sqrt(w @ Sigma @ w)
        if vol < 1e-10:
            return 1e10
        return -(ret - rf) / vol

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = Bounds(-0.5, 1.0) if allow_short else Bounds(0.0, 1.0)
    w0 = np.ones(n) / n

    try:
        result = minimize(
            _neg_sharpe, w0, method="SLSQP",
            bounds=bounds, constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-12},
        )
        if result.success:
            w = result.x
            ret = w @ mu
            vol = np.sqrt(w @ Sigma @ w)
            return {
                "weights": w,
                "ret": ret,
                "vol": vol,
                "sharpe": (ret - rf) / vol if vol > 1e-10 else 0.0,
            }
    except Exception:
        pass
    return None


def min_vol(
    mu: np.ndarray,
    Sigma: np.ndarray,
    allow_short: bool,
    rf: float = 0.0,
) -> Optional[Dict]:
    """Find the minimum volatility portfolio."""
    n = len(mu)

    def _vol(w):
        return np.sqrt(w @ Sigma @ w)

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = Bounds(-0.5, 1.0) if allow_short else Bounds(0.0, 1.0)
    w0 = np.ones(n) / n

    try:
        result = minimize(
            _vol, w0, method="SLSQP",
            bounds=bounds, constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-12},
        )
        if result.success:
            w = result.x
            ret = w @ mu
            vol = np.sqrt(w @ Sigma @ w)
            return {
                "weights": w,
                "ret": ret,
                "vol": vol,
                "sharpe": (ret - rf) / vol if vol > 1e-10 else 0.0,
            }
    except Exception:
        pass
    return None


def _min_vol_for_target(
    target_ret: float,
    mu: np.ndarray,
    Sigma: np.ndarray,
    allow_short: bool,
    rf: float = 0.0,
) -> Optional[Dict]:
    """Minimize volatility subject to a target return."""
    n = len(mu)

    def _vol_sq(w):
        return w @ Sigma @ w

    constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
        {"type": "eq", "fun": lambda w: w @ mu - target_ret},
    ]
    bounds = Bounds(-0.5, 1.0) if allow_short else Bounds(0.0, 1.0)
    w0 = np.ones(n) / n

    try:
        result = minimize(
            _vol_sq, w0, method="SLSQP",
            bounds=bounds, constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-12},
        )
        if result.success:
            w = result.x
            ret = w @ mu
            vol = np.sqrt(w @ Sigma @ w)
            return {
                "weights": w,
                "ret": ret,
                "vol": vol,
                "sharpe": (ret - rf) / vol if vol > 1e-10 else 0.0,
            }
    except Exception:
        pass
    return None


def efficient_frontier(
    mu: np.ndarray,
    Sigma: np.ndarray,
    rf: float,
    allow_short: bool,
    n_points: int = 100,
) -> Tuple[List[Dict], Optional[Dict], Optional[Dict], List[str]]:
    """Generate the efficient frontier via parameterized scan."""
    warnings: List[str] = []

    mv = min_vol(mu, Sigma, allow_short, rf)
    if mv is None:
        warnings.append("Min Vol optimization failed.")
        return [], None, None, warnings

    ms = max_sharpe(mu, Sigma, rf, allow_short)
    if ms is None:
        warnings.append("Max Sharpe optimization failed.")

    ret_min = mv["ret"]
    ret_max = max(np.max(mu), ms["ret"] if ms else np.max(mu)) * 1.05

    target_returns = np.linspace(ret_min, ret_max, n_points)
    frontier_points: List[Dict] = []

    for tr in target_returns:
        pt = _min_vol_for_target(tr, mu, Sigma, allow_short, rf)
        if pt is not None:
            frontier_points.append(pt)

    if len(frontier_points) < 5:
        warnings.append(
            "Efficient frontier could not be computed reliably. "
            "Check: (1) Are any two assets nearly identical? "
            "(2) Are forward return estimates plausible?"
        )
        return frontier_points, ms, mv, warnings

    return frontier_points, ms, mv, warnings


def compute_asset_points(
    mu: np.ndarray,
    sigma: np.ndarray,
    tickers: List[str],
) -> pd.DataFrame:
    """Build individual asset scatter points."""
    return pd.DataFrame({
        "ticker": tickers,
        "vol": sigma,
        "ret": mu,
    })


def compute_historical_mu_sigma(
    returns: pd.DataFrame,
    tickers: List[str],
    freq: int = 252,
) -> Tuple[pd.Series, pd.Series]:
    """Compute annualized historical returns (CAGR) and volatilities."""
    available = [t for t in tickers if t in returns.columns]
    daily_ret = returns[available]
    # CAGR: geometric annualized return, based on calendar time not row count
    total_log = daily_ret.sum()
    cal_years = (daily_ret.index[-1] - daily_ret.index[0]).days / 365.25
    ann_mu = np.exp(total_log / max(cal_years, 0.5)) - 1.0
    ann_sigma = daily_ret.std() * np.sqrt(freq)
    return ann_mu, ann_sigma
