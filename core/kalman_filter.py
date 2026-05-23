from typing import Dict

import numpy as np
import pandas as pd


def compute_obs(returns_i: pd.Series, returns_j: pd.Series) -> pd.Series:
    """Compute observation = product of two standardized return series."""
    common_idx = returns_i.index.intersection(returns_j.index)
    obs = returns_i.loc[common_idx] * returns_j.loc[common_idx]
    return obs


def kalman_filter_1d(
    obs: np.ndarray,
    Q: float = 0.001,
    R: float = 0.5,
    rho_init: float = 0.0,
    P_init: float = 1.0,
) -> Dict[str, np.ndarray]:
    """1D Kalman filter with phi=1 (random walk)."""
    T = len(obs)
    rho = np.zeros(T)
    P = np.zeros(T)
    K = np.zeros(T)

    rho_prev = rho_init
    P_prev = P_init

    for t in range(T):
        # Predict (phi = 1)
        rho_pred = rho_prev
        P_pred = P_prev + Q

        # Update
        if np.isnan(obs[t]):
            rho[t] = rho_pred
            P[t] = P_pred
            K[t] = 0.0
        else:
            K[t] = P_pred / (P_pred + R)
            rho[t] = rho_pred + K[t] * (obs[t] - rho_pred)
            P[t] = (1.0 - K[t]) * P_pred

        rho_prev = rho[t]
        P_prev = P[t]

    rho = np.clip(rho, -1.0, 1.0)
    return {"rho": rho, "P": P, "K": K}
