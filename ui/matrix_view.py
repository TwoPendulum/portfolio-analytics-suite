from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def build_heatmap(matrix: pd.DataFrame, freq_label: str = "") -> go.Figure:
    """Build a Plotly annotated heatmap for a correlation matrix."""
    tickers = list(matrix.index)
    z = matrix.values

    # Custom colorscale: red(-1) → white(0) → blue(+1)
    custom_colorscale = [
        [0.0, "#B22222"],
        [0.25, "#E57373"],
        [0.5, "#FFFFFF"],
        [0.75, "#64B5F6"],
        [1.0, "#1E90FF"],
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=tickers,
        y=tickers,
        zmin=-1.0,
        zmax=1.0,
        colorscale=custom_colorscale,
        text=np.round(z, 2),
        texttemplate="%{text}",
        textfont=dict(color="#333333", size=11),
        hovertemplate="%{x} vs %{y}<br>ρ = %{z:.3f}<extra></extra>",
        colorbar=dict(
            title={"text": "ρ", "side": "right"},
            tickvals=[-1.0, -0.5, 0.0, 0.5, 1.0],
            ticktext=["-1.0", "-0.5", "0.0", "0.5", "1.0"],
        ),
    ))

    title_text = f"Correlation Matrix — {freq_label}" if freq_label else "Correlation Matrix"
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E0E0E0",
        height=550,
        xaxis=dict(side="bottom", tickangle=-30),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10, r=10, t=40, b=10),
        title=title_text,
    )

    return fig


def render_correlation_matrix(
    freq: str,
    matrix: pd.DataFrame,
    rho_series: Dict[Tuple[str, str], pd.Series],
    obs_by_freq: Dict[Tuple[str, str], pd.Series],
    key_prefix: str = "matrix",
) -> None:
    """Render correlation matrix heatmap with click-to-select pair interaction."""
    freq_labels = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}
    label = freq_labels.get(freq, freq)

    tickers = list(matrix.index)
    if not tickers:
        st.info(f"No data for {label} frequency.")
        return

    col_left, col_right = st.columns([1, 3])

    with col_left:
        st.markdown("#### Select Pair")
        pair_options = ["—"] + [f"{a} vs {b}" for i, a in enumerate(tickers) for b in tickers[i+1:]]
        selected = st.selectbox(
            f"Click heatmap or select:",
            pair_options,
            key=f"{key_prefix}_pair_select_{freq}",
        )
        if selected and selected != "—":
            parts = selected.split(" vs ")
            st.session_state.selected_pair = (parts[0], parts[1])

    with col_right:
        fig = build_heatmap(matrix, freq_label=label)
        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_heatmap_{freq}")


def render_timeseries_section(
    pair: Tuple[str, str],
    rho_by_freq: Dict[str, Dict[Tuple[str, str], pd.Series]],
    obs_by_freq: Dict[str, Dict[Tuple[str, str], pd.Series]],
) -> None:
    """Render the timeseries chart for a selected pair below the heatmap."""
    from .timeseries_view import build_timeseries_figure

    ticker_i, ticker_j = pair
    st.markdown("---")
    st.subheader(f"Correlation Time Series: {ticker_i} vs {ticker_j}")

    rho_curves = {}
    obs_curves = {}
    for freq in ["daily", "weekly", "monthly"]:
        series = rho_by_freq.get(freq, {}).get(pair)
        if series is None:
            series = rho_by_freq.get(freq, {}).get((ticker_j, ticker_i))
        if series is not None:
            rho_curves[freq] = series
        obs = obs_by_freq.get(freq, {}).get(pair)
        if obs is None:
            obs = obs_by_freq.get(freq, {}).get((ticker_j, ticker_i))
        if obs is not None:
            obs_curves[freq] = obs

    if rho_curves:
        fig = build_timeseries_figure(
            rho_by_freq=rho_curves,
            obs_by_freq=obs_curves,
            pair=pair,
        )
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        for idx, freq in enumerate(["daily", "weekly", "monthly"]):
            col = [col1, col2][idx % 2]
            s = rho_curves.get(freq)
            if s is not None and len(s) > 0:
                with col:
                    rho_latest = s.values[-1]
                    delta = s.values[-1] - s.values[-min(22, len(s))]
                    st.metric(
                        f"{freq.title()} ρ (latest)",
                        f"{rho_latest:.3f}",
                        f"{delta:+.3f} (1M change)",
                    )
    else:
        st.info("No timeseries data available for this pair.")

    if st.button("Clear Selection", key="clear_pair_btn"):
        st.session_state.selected_pair = None
        st.rerun()
