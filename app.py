import itertools

import numpy as np
import pandas as pd
import streamlit as st

from core.correlation import compute_correlation_pipeline
from core.data_loader import fetch_data, load_asset_config
from core.optimizer import (
    build_cov_matrix,
    compute_asset_points,
    compute_historical_mu_sigma,
    efficient_frontier,
)
from ui.frontier_view import build_weights_bar, render_frontier_plot, render_weight_input
from ui.matrix_view import (
    build_heatmap,
    render_correlation_matrix,
    render_timeseries_section,
)
from ui.methodology_view import render_methodology


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Portfolio Analytics Suite",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Session state init ──────────────────────────────────────────────────────
def init_session_state():
    defaults = {
        "returns": None,
        "latest_matrices": None,
        "rho_series": None,
        "obs_by_freq": None,
        "active_tickers": [],
        "selected_pair": None,
        "ef_result": None,
        "custom_weights": None,
        "allow_short": False,
        "rf_rate": 4.5,
        "computation_warnings": [],
        "computed_once": False,
        "run_counter": 0,
        "forward_mu_df": None,
        "forward_sigma_df": None,
        "manual_cell_mask": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
        padding: 8px 20px;
        font-size: 0.95rem;
    }
    div[data-testid="stSidebarNav"] { display: none; }
    .stButton button[kind="primary"] {
        background: linear-gradient(90deg, #4A90D9, #357ABD);
        border: none;
        font-weight: 600;
    }
    .stButton button[kind="secondary"] {
        border: 1px solid #4A90D9;
        color: #4A90D9;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ─────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("## Portfolio Analytics")
        st.markdown("---")

        # Asset config
        config = load_asset_config()
        all_assets = pd.DataFrame(config)

        # Group filter
        groups = all_assets["group"].unique().tolist()
        selected_groups = st.multiselect(
            "Asset Groups",
            groups,
            default=groups,
            key="sidebar_groups",
        )

        filtered = all_assets[all_assets["group"].isin(selected_groups)]
        asset_options = [f"{row['ticker']} — {row['name']}" for _, row in filtered.iterrows()]
        default_assets = asset_options[:min(len(asset_options), 10)]
        selected_assets = st.multiselect(
            "Select Assets",
            asset_options,
            default=default_assets,
            key="sidebar_assets",
        )

        tickers = [s.split(" — ")[0] for s in selected_assets]

        # Date range
        today = pd.Timestamp.today()
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                today - pd.DateOffset(years=5),
                key="sidebar_start",
            )
        with col2:
            end_date = st.date_input("End Date", today, key="sidebar_end")

        # Advanced parameters (collapsible)
        with st.expander("Advanced Parameters", expanded=False):
            Q = st.slider(
                "Q (process noise)",
                0.0001, 0.1, 0.001,
                format="%.4f",
                help="Higher Q = more responsive to recent observations.",
                key="sidebar_Q",
            )
            R = st.slider(
                "R (observation noise)",
                0.01, 2.0, 0.5,
                format="%.2f",
                help="Higher R = smoother estimates, less responsive to noise.",
                key="sidebar_R",
            )

        st.markdown("---")

        col_run, _ = st.columns([1, 1])
        with col_run:
            run_clicked = st.button(
                "Run Computation",
                type="primary",
                use_container_width=True,
                key="sidebar_run",
            )

        if len(tickers) < 2:
            st.caption("Select at least 2 assets to run computation.")

        return tickers, str(start_date), str(end_date), Q, R, run_clicked


# ── Tab 1: Dynamic Correlation Tracking ─────────────────────────────────────
def render_tab1():
    st.header("Dynamic Correlation Tracking")

    if not st.session_state.computed_once:
        st.info("Click **Run Computation** in the sidebar to get started.")
        return

    # Warnings
    for w in st.session_state.computation_warnings:
        st.warning(w)

    # Sub-tabs
    freq_keys = ["daily", "weekly", "monthly"]
    freq_labels = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}
    tabs = st.tabs([freq_labels[k] for k in freq_keys])

    for tab, freq in zip(tabs, freq_keys):
        with tab:
            matrix = st.session_state.latest_matrices.get(freq)
            if matrix is None or matrix.empty:
                st.info(f"No data available for {freq_labels[freq]} frequency.")
                continue

            render_correlation_matrix(
                freq=freq,
                matrix=matrix,
                rho_series=st.session_state.rho_series.get(freq, {}),
                obs_by_freq=st.session_state.obs_by_freq.get(freq, {}),
                key_prefix="tab1",
            )

    # Selected pair timeseries
    if st.session_state.selected_pair:
        render_timeseries_section(
            pair=st.session_state.selected_pair,
            rho_by_freq=st.session_state.rho_series or {},
            obs_by_freq=st.session_state.obs_by_freq or {},
        )


# ── Tab 2: Efficient Frontier ───────────────────────────────────────────────
def render_tab2():
    st.header("Efficient Frontier")

    if not st.session_state.computed_once:
        st.info("Run computation in **Dynamic Correlation Tracking** tab first (click Run in sidebar).")
        return

    tickers = st.session_state.active_tickers
    if not tickers or len(tickers) < 2:
        st.warning("At least 2 assets required.")
        return

    monthly_matrix = st.session_state.latest_matrices.get("monthly")
    if monthly_matrix is None:
        st.warning("Monthly correlation matrix not available. Try recomputing with sufficient data.")
        return

    # Ensure all active tickers are in the matrix
    available_tickers = [t for t in tickers if t in monthly_matrix.index]
    if len(available_tickers) < 2:
        st.warning("Not enough tickers available in the monthly correlation matrix.")
        return
    tickers = available_tickers

    # ── Forward Estimates Section ──
    st.subheader("Forward Estimates")

    st.markdown("""
    Enter forward expected returns (μ) and volatilities (σ).
    Click **Auto-fill from History** to populate with historical estimates, then manually adjust any cell.
    Manually edited cells are highlighted.
    """)

    # Auto-fill button
    col_fill, col_rf = st.columns([1, 3])
    with col_fill:
        auto_fill = st.button("Auto-fill from History", use_container_width=True, key="auto_fill_btn")
    with col_rf:
        rf_rate = st.number_input(
            "Risk-Free Rate (%)",
            min_value=0.0, max_value=20.0,
            value=st.session_state.rf_rate,
            step=0.1,
            format="%.1f",
            key="rf_input",
        )
        st.session_state.rf_rate = rf_rate

    # Initialize forward estimates if needed
    if auto_fill or st.session_state.forward_mu_df is None:
        with st.spinner("Computing historical estimates..."):
            ann_mu, ann_sigma = compute_historical_mu_sigma(
                st.session_state.returns, tickers
            )
            st.session_state.forward_mu_df = ann_mu * 100  # convert to %
            st.session_state.forward_sigma_df = ann_sigma * 100
            if "manual_cell_mask" not in st.session_state:
                st.session_state.manual_cell_mask = set()
            if auto_fill:
                st.session_state.manual_cell_mask = set()

    # Build the combined input table
    names_map = {a["ticker"]: a["name"] for a in load_asset_config()}
    table_data = []
    for t in tickers:
        mu_val = st.session_state.forward_mu_df.get(t, 0.0)
        sigma_val = st.session_state.forward_sigma_df.get(t, 20.0)
        table_data.append({
            "Ticker": t,
            "Name": names_map.get(t, t),
            "Include": True,
            "Forward μ (%)": round(float(mu_val), 2),
            "Forward σ (%)": round(float(sigma_val), 2),
            "Allow Short": st.session_state.allow_short,
        })

    input_df = pd.DataFrame(table_data)

    edited_df = st.data_editor(
        input_df,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", disabled=True),
            "Name": st.column_config.TextColumn("Name", disabled=True),
            "Include": st.column_config.CheckboxColumn(
                "Include",
                help="Uncheck to exclude this asset from the optimization.",
                default=True,
            ),
            "Forward μ (%)": st.column_config.NumberColumn(
                "Forward μ (%)",
                min_value=-100.0,
                max_value=1000.0,
                step=0.1,
                format="%.2f",
            ),
            "Forward σ (%)": st.column_config.NumberColumn(
                "Forward σ (%)",
                min_value=0.1,
                max_value=500.0,
                step=0.1,
                format="%.2f",
            ),
            "Allow Short": st.column_config.CheckboxColumn(
                "Allow Short",
                help="Allow short selling for this asset (weight ≥ -50%).",
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="forward_editor",
    )

    # Detect manual edits
    for i, row in edited_df.iterrows():
        t = row["Ticker"]
        orig_mu = input_df.loc[i, "Forward μ (%)"]
        orig_sigma = input_df.loc[i, "Forward σ (%)"]
        if abs(row["Forward μ (%)"] - orig_mu) > 0.01:
            st.session_state.manual_cell_mask.add((t, "mu"))
        if abs(row["Forward σ (%)"] - orig_sigma) > 0.01:
            st.session_state.manual_cell_mask.add((t, "sigma"))

    # Update stored values
    for _, row in edited_df.iterrows():
        t = row["Ticker"]
        st.session_state.forward_mu_df[t] = row["Forward μ (%)"]
        st.session_state.forward_sigma_df[t] = row["Forward σ (%)"]

    # Allow short toggle per-asset
    st.session_state.allow_short = edited_df["Allow Short"].any()

    # Highlight note
    if st.session_state.manual_cell_mask:
        st.caption("Manually edited cells are highlighted with a marker.")

    # ── Compute EF ──
    st.markdown("---")

    # Filter to included assets only
    included_mask = edited_df["Include"].values if "Include" in edited_df.columns else [True] * len(tickers)
    ef_tickers = [t for t, inc in zip(tickers, included_mask) if inc]
    excluded_count = len(tickers) - len(ef_tickers)
    if excluded_count > 0:
        st.caption(f"{excluded_count} asset(s) excluded from optimization.")

    if len(ef_tickers) < 2:
        st.warning("At least 2 assets must be included to compute the efficient frontier.")
    elif st.button("Compute Efficient Frontier", type="primary", key="compute_ef_btn"):
        with st.spinner("Computing efficient frontier..."):
            mu = np.array([st.session_state.forward_mu_df[t] / 100.0 for t in ef_tickers])
            sigma = np.array([st.session_state.forward_sigma_df[t] / 100.0 for t in ef_tickers])
            rho_vals = monthly_matrix.loc[ef_tickers, ef_tickers].values
            rf = rf_rate / 100.0

            Sigma = build_cov_matrix(sigma, rho_vals)
            allow_short_any = st.session_state.allow_short

            ef_points, ms_pt, mv_pt, ef_warnings = efficient_frontier(
                mu, Sigma, rf, allow_short_any, n_points=100,
            )

            for w in ef_warnings:
                st.warning(w)

            asset_pts = compute_asset_points(mu, sigma, ef_tickers)

            st.session_state.ef_result = {
                "ef_points": ef_points,
                "max_sharpe": ms_pt,
                "min_vol": mv_pt,
                "asset_points": asset_pts,
                "tickers": ef_tickers,
            }

    # ── Render EF ──
    if st.session_state.ef_result:
        ef = st.session_state.ef_result
        ef_tickers_rendered = ef["tickers"]

        # Custom portfolio section
        col_ef, col_spacer = st.columns([3, 1])
        with col_ef:
            custom_wts = render_weight_input(
                ef_tickers_rendered,
                names=[names_map.get(t, t) for t in ef_tickers_rendered],
                key="custom_weight_editor",
            )

        if custom_wts:
            mu_arr = np.array([st.session_state.forward_mu_df[t] / 100.0 for t in ef_tickers_rendered])
            sigma_arr = np.array([st.session_state.forward_sigma_df[t] / 100.0 for t in ef_tickers_rendered])
            rho_vals = monthly_matrix.loc[ef_tickers_rendered, ef_tickers_rendered].values
            Sigma = build_cov_matrix(sigma_arr, rho_vals)

            w_arr = np.array([custom_wts[t] / 100.0 for t in ef_tickers_rendered])
            ret = w_arr @ mu_arr
            vol = np.sqrt(w_arr @ Sigma @ w_arr)
            sharpe = (ret - rf_rate / 100.0) / vol if vol > 1e-10 else 0.0

            st.session_state.custom_weights = {
                "weights": custom_wts,
                "ret": ret,
                "vol": vol,
                "sharpe": sharpe,
            }

        render_frontier_plot(
            ef_points=ef["ef_points"],
            max_sharpe_pt=ef["max_sharpe"],
            min_vol_pt=ef["min_vol"],
            asset_points=ef["asset_points"],
            tickers=ef_tickers_rendered,
            custom_portfolio=st.session_state.custom_weights,
            rf=rf_rate / 100.0,
        )

        # Show custom portfolio stats
        if st.session_state.custom_weights:
            cw = st.session_state.custom_weights
            st.markdown("---")
            st.markdown("**Your Custom Portfolio**")
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Expected Return", f"{cw['ret']:.2%}")
            mc2.metric("Volatility", f"{cw['vol']:.2%}")
            mc3.metric("Sharpe Ratio", f"{cw['sharpe']:.3f}")


# ── Tab 3: Methodology ─────────────────────────────────────────────────────
def render_tab3():
    render_methodology(docs_dir="docs")


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    # Sidebar
    tickers, start_date, end_date, Q, R, run_clicked = render_sidebar()

    # Tab navigation
    tab1, tab2, tab3 = st.tabs([
        "Dynamic Correlation Tracking",
        "Efficient Frontier",
        "Methodology",
    ])

    # Run computation
    if run_clicked:
        if len(tickers) < 2:
            st.sidebar.error("Please select at least 2 assets.")
        else:
            with st.spinner("Fetching data and computing dynamic correlations... This may take up to 60 seconds."):
                try:
                    returns, data_warnings = fetch_data(tickers, start_date, end_date)
                    warnings_list = list(data_warnings)

                    matrices, rho_series, obs_by_freq, corr_warnings = compute_correlation_pipeline(
                        returns, Q=Q, R=R,
                    )
                    warnings_list.extend(corr_warnings)

                    st.session_state.returns = returns
                    st.session_state.latest_matrices = matrices
                    st.session_state.rho_series = rho_series
                    st.session_state.obs_by_freq = obs_by_freq
                    st.session_state.active_tickers = tickers
                    st.session_state.computation_warnings = warnings_list
                    st.session_state.computed_once = True
                    st.session_state.run_counter += 1
                    st.session_state.ef_result = None
                    st.session_state.custom_weights = None
                    st.session_state.forward_mu_df = None
                    st.session_state.forward_sigma_df = None
                    st.session_state.manual_cell_mask = set()

                except Exception as e:
                    st.sidebar.error(f"Computation failed: {e}")

    # Show status in sidebar
    if st.session_state.computed_once:
        st.sidebar.success(f"Active: {len(st.session_state.active_tickers)} assets")
        if st.session_state.latest_matrices:
            freqs = list(st.session_state.latest_matrices.keys())
            st.sidebar.caption(f"Frequencies: {', '.join(freqs)}")

    # Render tabs
    with tab1:
        render_tab1()
    with tab2:
        render_tab2()
    with tab3:
        render_tab3()


if __name__ == "__main__":
    main()
