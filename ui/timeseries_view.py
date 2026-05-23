from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go


def build_timeseries_figure(
    rho_by_freq: Dict[str, pd.Series],
    obs_by_freq: Optional[Dict[str, pd.Series]] = None,
    pair: Tuple[str, str] = ("", ""),
    title: str = "",
) -> go.Figure:
    """Build a Plotly figure with multi-frequency rho curves, obs scatter, and reference lines."""
    freq_colors = {"daily": "#4A90D9", "weekly": "#50C878", "monthly": "#FFA500"}
    freq_widths = {"daily": 2.0, "weekly": 1.5, "monthly": 1.5}
    freq_dash = {"daily": "solid", "weekly": "solid", "monthly": "dash"}
    freq_labels = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}

    fig = go.Figure()

    # Reference lines at ±1
    for y, label in [(-1.0, "ρ = -1"), (1.0, "ρ = +1")]:
        fig.add_hline(
            y=y, line_dash="dash", line_color="gray",
            opacity=0.3, annotation_text=label,
            annotation_position="top right",
        )

    # Rho curves for each frequency
    for freq in ["daily", "weekly", "monthly"]:
        series = rho_by_freq.get(freq)
        if series is None or series.empty:
            continue
        fig.add_trace(go.Scatter(
            x=series.index, y=series.values,
            mode="lines",
            name=freq_labels[freq],
            line=dict(color=freq_colors[freq], width=freq_widths[freq], dash=freq_dash[freq]),
            hovertemplate=f"{freq_labels[freq]}: %{{y:.3f}}<br>%{{x}}<extra></extra>",
        ))
        # Latest value annotation
        if len(series) > 0:
            fig.add_annotation(
                x=series.index[-1], y=series.values[-1],
                text=f"{series.values[-1]:.2f}",
                showarrow=False,
                xanchor="left",
                font=dict(color=freq_colors[freq], size=11),
            )

    # Obs scatter (semi-transparent)
    if obs_by_freq:
        for freq in ["daily", "weekly", "monthly"]:
            obs_series = obs_by_freq.get(freq)
            if obs_series is None or obs_series.empty:
                continue
            fig.add_trace(go.Scatter(
                x=obs_series.index, y=obs_series.values,
                mode="markers",
                name=f"Obs ({freq_labels[freq]})",
                marker=dict(color="gray", size=2, opacity=0.12),
                showlegend=False,
                hovertemplate=f"Obs: %{{y:.3f}}<br>%{{x}}<extra></extra>",
            ))

    title_text = title or f"Correlation Time Series: {pair[0]} vs {pair[1]}"
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E0E0E0",
        height=450,
        hovermode="x unified",
        legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"),
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis=dict(range=[-1.25, 1.25], title="Correlation (ρ)", gridcolor="#2D2D44"),
        xaxis=dict(title="", gridcolor="#2D2D44"),
        title=title_text,
    )

    return fig
