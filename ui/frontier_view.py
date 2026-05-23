from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def build_frontier_figure(
    ef_points: List[Dict],
    max_sharpe_pt: Optional[Dict],
    min_vol_pt: Optional[Dict],
    asset_points: pd.DataFrame,
    custom_portfolio: Optional[Dict] = None,
    rf: float = 0.0,
) -> go.Figure:
    """Build the efficient frontier Plotly figure."""
    fig = go.Figure()

    # Frontier curve
    if ef_points:
        vols = [p["vol"] for p in ef_points]
        rets = [p["ret"] for p in ef_points]
        sharpes = [p["sharpe"] for p in ef_points]

        fig.add_trace(go.Scatter(
            x=vols, y=rets,
            mode="lines+markers",
            name="Efficient Frontier",
            line=dict(color="#4A90D9", width=2.5),
            marker=dict(
                size=4, color=sharpes,
                colorscale="RdYlBu",
                showscale=True,
                colorbar=dict(title="Sharpe", x=1.02),
            ),
            hovertemplate="Vol: %{x:.2%}<br>Ret: %{y:.2%}<br>Sharpe: %{marker.color:.3f}<extra></extra>",
        ))

    # Max Sharpe point
    if max_sharpe_pt:
        fig.add_trace(go.Scatter(
            x=[max_sharpe_pt["vol"]], y=[max_sharpe_pt["ret"]],
            mode="markers+text",
            name="Max Sharpe",
            marker=dict(symbol="star", size=18, color="#FFD700", line=dict(width=1, color="#333")),
            text=["Max Sharpe"],
            textposition="top center",
            hovertemplate="Max Sharpe<br>Vol: %{x:.2%}<br>Ret: %{y:.2%}<br>Sharpe: %{customdata:.3f}<extra></extra>",
            customdata=[max_sharpe_pt["sharpe"]],
        ))

    # Min Vol point
    if min_vol_pt:
        fig.add_trace(go.Scatter(
            x=[min_vol_pt["vol"]], y=[min_vol_pt["ret"]],
            mode="markers+text",
            name="Min Vol",
            marker=dict(symbol="diamond", size=14, color="#00FF7F", line=dict(width=1, color="#333")),
            text=["Min Vol"],
            textposition="bottom center",
            hovertemplate="Min Vol<br>Vol: %{x:.2%}<br>Ret: %{y:.2%}<br>Sharpe: %{customdata:.3f}<extra></extra>",
            customdata=[min_vol_pt["sharpe"]],
        ))

    # Individual assets
    if not asset_points.empty:
        fig.add_trace(go.Scatter(
            x=asset_points["vol"], y=asset_points["ret"],
            mode="markers+text",
            name="Assets",
            marker=dict(symbol="circle", size=10, color="#B0BEC5"),
            text=asset_points["ticker"],
            textposition="top center",
            hovertemplate="%{text}<br>Vol: %{x:.2%}<br>Ret: %{y:.2%}<extra></extra>",
        ))

    # Custom portfolio
    if custom_portfolio:
        fig.add_trace(go.Scatter(
            x=[custom_portfolio["vol"]], y=[custom_portfolio["ret"]],
            mode="markers+text",
            name="Custom Portfolio",
            marker=dict(symbol="x", size=16, color="#FF69B4", line=dict(width=2, color="#333")),
            text=["Your Portfolio"],
            textposition="top center",
            hovertemplate="Custom Portfolio<br>Vol: %{x:.2%}<br>Ret: %{y:.2%}<br>Sharpe: %{customdata:.3f}<extra></extra>",
            customdata=[custom_portfolio["sharpe"]],
        ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E0E0E0",
        height=600,
        hovermode="closest",
        xaxis=dict(title="Annualized Volatility", tickformat=".0%", gridcolor="#2D2D44"),
        yaxis=dict(title="Annualized Expected Return", tickformat=".0%", gridcolor="#2D2D44"),
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center"),
    )

    return fig


def build_weights_bar(weights: np.ndarray, tickers: List[str]) -> go.Figure:
    """Horizontal bar chart of portfolio weights."""
    colors = ["#4A90D9" if w >= 0 else "#B22222" for w in weights]

    fig = go.Figure(go.Bar(
        x=weights, y=tickers,
        orientation="h",
        marker_color=colors,
        text=[f"{w:.1%}" for w in weights],
        textposition="outside",
        hovertemplate="%{y}: %{x:.2%}<extra></extra>",
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E0E0E0",
        height=300,
        xaxis=dict(title="Weight", tickformat=".0%", gridcolor="#2D2D44"),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
    )

    return fig


def render_frontier_plot(
    ef_points: List[Dict],
    max_sharpe_pt: Optional[Dict],
    min_vol_pt: Optional[Dict],
    asset_points: pd.DataFrame,
    tickers: List[str],
    custom_portfolio: Optional[Dict] = None,
    rf: float = 0.0,
) -> None:
    """Render the efficient frontier chart and handle point-click for weights."""
    fig = build_frontier_figure(ef_points, max_sharpe_pt, min_vol_pt, asset_points, custom_portfolio, rf)

    # Use session state to track selected frontier index
    if "frontier_point_index" not in st.session_state:
        st.session_state.frontier_point_index = None

    st.plotly_chart(fig, use_container_width=True, key="frontier_chart")

    # Let user select a frontier point by index
    st.caption("Select a frontier point to view its portfolio weights:")
    n = len(ef_points)
    if n > 0:
        selected_idx = st.slider(
            "Frontier Point", 0, n - 1,
            value=st.session_state.frontier_point_index or 0,
            key="frontier_slider",
        )
        st.session_state.frontier_point_index = selected_idx
        point = ef_points[selected_idx]

        st.markdown(f"**Point {selected_idx + 1}/{n}** — Vol: {point['vol']:.2%}, "
                    f"Ret: {point['ret']:.2%}, Sharpe: {point['sharpe']:.3f}")

        fig_w = build_weights_bar(point["weights"], tickers)
        st.plotly_chart(fig_w, use_container_width=True, key="frontier_weights_bar")

    # Show Max Sharpe and Min Vol weights
    col_ms, col_mv = st.columns(2)
    if max_sharpe_pt:
        with col_ms:
            st.markdown("**Max Sharpe Portfolio**")
            fig_ms = build_weights_bar(max_sharpe_pt["weights"], tickers)
            st.plotly_chart(fig_ms, use_container_width=True, key="ms_weights_bar")
    if min_vol_pt:
        with col_mv:
            st.markdown("**Min Vol Portfolio**")
            fig_mv = build_weights_bar(min_vol_pt["weights"], tickers)
            st.plotly_chart(fig_mv, use_container_width=True, key="mv_weights_bar")


def render_weight_input(
    tickers: List[str],
    names: Optional[List[str]] = None,
    key: str = "weight_editor",
) -> Optional[Dict[str, float]]:
    """Render a weight input table for custom portfolio with validation."""
    if names is None:
        names = tickers

    n = len(tickers)
    default_wt = 100.0 / n

    st.markdown("#### Custom Portfolio Weights")

    data = {"Ticker": tickers, "Name": names, "Weight (%)": [round(default_wt, 1)] * n}
    df = pd.DataFrame(data)

    edited_df = st.data_editor(
        df,
        column_config={
            "Ticker": st.column_config.TextColumn(disabled=True),
            "Name": st.column_config.TextColumn(disabled=True),
            "Weight (%)": st.column_config.NumberColumn(
                min_value=-50.0,
                max_value=100.0,
                step=0.1,
                format="%.1f",
            ),
        },
        hide_index=True,
        use_container_width=True,
        key=key,
    )

    total = edited_df["Weight (%)"].sum()
    is_valid = abs(total - 100.0) < 0.05

    if is_valid:
        st.success(f"Weights sum to {total:.1f}%")
    else:
        st.error(f"Weights sum to {total:.1f}%. Must equal 100%.")

    if st.button("Plot Custom Portfolio", disabled=not is_valid, type="secondary"):
        weights = dict(zip(edited_df["Ticker"], edited_df["Weight (%)"]))
        return weights

    return None
