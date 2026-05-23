import itertools
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .garch_filter import garch_standardize
from .kalman_filter import compute_obs, kalman_filter_1d


def _resample_returns(returns: pd.DataFrame, freq: str) -> pd.DataFrame:
    if freq == "daily":
        return returns.copy()
    elif freq == "weekly":
        return returns.resample("W-FRI").apply(lambda x: x.sum())
    elif freq == "monthly":
        return returns.resample("ME").apply(lambda x: x.sum())
    else:
        raise ValueError(f"Unknown frequency: {freq}")


def compute_correlation_pipeline(
    returns: pd.DataFrame,
    frequencies: Optional[List[str]] = None,
    Q: float = 0.001,
    R: float = 0.5,
    max_workers: Optional[int] = None,
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Dict[Tuple[str, str], pd.Series]], List[str]]:
    """Main pipeline: GARCH-standardize all tickers at all frequencies, then pairwise KF."""
    if frequencies is None:
        frequencies = ["daily", "weekly", "monthly"]
    if max_workers is None:
        max_workers = min(8, os.cpu_count() or 4)

    all_warnings: List[str] = []

    # Step 1: Resample returns
    returns_by_freq: Dict[str, pd.DataFrame] = {}
    for freq in frequencies:
        resampled = _resample_returns(returns, freq)
        if len(resampled) < 10:
            all_warnings.append(f"{freq}: too few observations after resampling ({len(resampled)}).")
            continue
        returns_by_freq[freq] = resampled

    if not returns_by_freq:
        return {}, {}, all_warnings

    # Step 2: GARCH on all (freq, ticker) combinations
    garch_results: Dict[str, Dict[str, Tuple[pd.Series, pd.Series]]] = {}
    tasks = []
    for freq, ret_df in returns_by_freq.items():
        garch_results[freq] = {}
        for ticker in ret_df.columns:
            tasks.append((freq, ticker, ret_df[ticker]))

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {
            ex.submit(garch_standardize, task[2]): (task[0], task[1])
            for task in tasks
        }
        for fut in as_completed(futures):
            freq, ticker = futures[fut]
            try:
                std, vol, warn = fut.result()
                garch_results[freq][ticker] = (std, vol)
                if warn:
                    all_warnings.append(f"[{freq}] {ticker}: {warn}")
            except Exception as e:
                all_warnings.append(f"[{freq}] {ticker}: GARCH failed — {e}. Using EWMA fallback.")
                ret = returns_by_freq[freq][ticker].dropna()
                from .garch_filter import _ewma_fallback
                fb = _ewma_fallback(ret.values)
                std = pd.Series(ret.values / fb, index=ret.index)
                vol = pd.Series(fb, index=ret.index)
                garch_results[freq][ticker] = (std, vol)

    # Step 3: Pairwise Kalman Filter
    rho_series: Dict[str, Dict[Tuple[str, str], pd.Series]] = {}
    latest_matrices: Dict[str, pd.DataFrame] = {}

    for freq, ret_df in returns_by_freq.items():
        tickers_list = list(ret_df.columns)
        if len(tickers_list) < 2:
            all_warnings.append(f"{freq}: fewer than 2 tickers available; skipping.")
            continue

        n = len(tickers_list)
        rho_series[freq] = {}

        # Build pair tasks
        pair_tasks = list(itertools.combinations(tickers_list, 2))

        pair_results: Dict[Tuple[str, str], np.ndarray] = {}
        pair_indices: Dict[Tuple[str, str], pd.DatetimeIndex] = {}

        def _run_kf_pair(i, j, freq=freq):
            g_i = garch_results.get(freq, {}).get(i)
            g_j = garch_results.get(freq, {}).get(j)
            if g_i is None or g_j is None:
                return None
            std_i, _ = g_i
            std_j, _ = g_j
            obs = compute_obs(std_i, std_j)
            if len(obs) < 10:
                return None
            # Initial rho from historical Pearson correlation on overlapping data
            common_idx = std_i.index.intersection(std_j.index)
            hist_corr = std_i.loc[common_idx].corr(std_j.loc[common_idx])
            if np.isnan(hist_corr):
                hist_corr = 0.0
            ovals = obs.values if hasattr(obs, 'values') else obs
            result = kalman_filter_1d(ovals, Q=Q, R=R, rho_init=float(hist_corr), P_init=0.1)
            return (i, j, result["rho"], obs.index)

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_run_kf_pair, i, j): (i, j) for (i, j) in pair_tasks}
            for fut in as_completed(futures):
                res = fut.result()
                if res is None:
                    continue
                i, j, rho_arr, idx = res
                pair_results[(i, j)] = rho_arr
                pair_indices[(i, j)] = idx

        # Build matrix
        matrix = pd.DataFrame(np.eye(n), index=tickers_list, columns=tickers_list)
        for (i, j), rho_arr in pair_results.items():
            if len(rho_arr) > 0:
                latest = rho_arr[-1]
                matrix.loc[i, j] = latest
                matrix.loc[j, i] = latest
                # Store series for both directions
                series = pd.Series(rho_arr, index=pair_indices[(i, j)])
                rho_series[freq][(i, j)] = series
                rho_series[freq][(j, i)] = pd.Series(rho_arr[::-1], index=pair_indices[(i, j)][::-1])

        latest_matrices[freq] = matrix

    # Build obs_by_freq from garch results
    obs_by_freq: Dict[str, Dict[Tuple[str, str], pd.Series]] = {}
    for freq in frequencies:
        if freq not in returns_by_freq:
            continue
        obs_by_freq[freq] = {}
        ret_df = returns_by_freq[freq]
        for i, j in itertools.combinations(ret_df.columns, 2):
            gi = garch_results.get(freq, {}).get(i)
            gj = garch_results.get(freq, {}).get(j)
            if gi is not None and gj is not None:
                obs_by_freq[freq][(i, j)] = compute_obs(gi[0], gj[0])

    return latest_matrices, rho_series, obs_by_freq, all_warnings
