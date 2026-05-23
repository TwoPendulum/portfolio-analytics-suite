"use client";

import dynamic from "next/dynamic";
import { FrontierResponse, PortfolioPoint } from "@/lib/types";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface Props {
  data: FrontierResponse;
  customPortfolio: { ret: number; vol: number; sharpe: number } | null;
}

export default function FrontierPlot({ data, customPortfolio }: Props) {
  const { efPoints, maxSharpe, minVol, assetPoints } = data;
  const traces: any[] = [];

  // Frontier curve
  if (efPoints.length > 0) {
    const vols = efPoints.map((p) => p.vol);
    const rets = efPoints.map((p) => p.ret);
    const sharpes = efPoints.map((p) => p.sharpe);
    traces.push({
      type: "scatter",
      x: vols, y: rets,
      mode: "lines+markers",
      name: "Efficient Frontier",
      line: { color: "#4A90D9", width: 2.5 },
      marker: {
        size: 4, color: sharpes,
        colorscale: [[0, "#B22222"], [0.5, "#FFFFFF"], [1, "#1E90FF"]], showscale: true,
        colorbar: { title: "Sharpe", x: 1.02 },
      },
      hovertemplate: "Vol: %{x:.2%}<br>Ret: %{y:.2%}<br>Sharpe: %{marker.color:.3f}<extra></extra>",
    });
  }

  // Max Sharpe
  if (maxSharpe) {
    traces.push({
      type: "scatter",
      x: [maxSharpe.vol], y: [maxSharpe.ret],
      mode: "markers+text",
      name: "Max Sharpe",
      marker: { symbol: "star", size: 18, color: "#FFD700" },
      text: ["Max Sharpe"], textposition: "top center",
      hovertemplate: "Max Sharpe<br>Vol: %{x:.2%}<br>Ret: %{y:.2%}<extra></extra>",
    });
  }

  // Min Vol
  if (minVol) {
    traces.push({
      type: "scatter",
      x: [minVol.vol], y: [minVol.ret],
      mode: "markers+text",
      name: "Min Vol",
      marker: { symbol: "diamond", size: 14, color: "#00FF7F" },
      text: ["Min Vol"], textposition: "bottom center",
      hovertemplate: "Min Vol<br>Vol: %{x:.2%}<br>Ret: %{y:.2%}<extra></extra>",
    });
  }

  // Assets
  if (assetPoints && assetPoints.tickers.length > 0) {
    traces.push({
      type: "scatter",
      x: assetPoints.vol, y: assetPoints.ret,
      mode: "markers+text",
      name: "Assets",
      marker: { symbol: "circle", size: 10, color: "#B0BEC5" },
      text: assetPoints.tickers, textposition: "top center",
      hovertemplate: "%{text}<br>Vol: %{x:.2%}<br>Ret: %{y:.2%}<extra></extra>",
    });
  }

  // Custom portfolio
  if (customPortfolio) {
    traces.push({
      type: "scatter",
      x: [customPortfolio.vol], y: [customPortfolio.ret],
      mode: "markers+text",
      name: "Your Portfolio",
      marker: { symbol: "x", size: 16, color: "#FF69B4" },
      text: ["Your Portfolio"], textposition: "top center",
      hovertemplate: "Custom<br>Vol: %{x:.2%}<br>Ret: %{y:.2%}<extra></extra>",
    });
  }

  return (
    <Plot
      data={traces}
      layout={{
        template: "plotly_dark",
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: "#E0E0E0" },
        height: 500,
        hovermode: "closest",
        xaxis: { title: "Annualized Volatility", tickformat: ".0%", gridcolor: "#2D2D44", automargin: true },
        yaxis: { title: "Annualized Expected Return", tickformat: ".0%", gridcolor: "#2D2D44", automargin: true },
        margin: { l: 70, r: 20, t: 10, b: 50 },
        legend: { orientation: "h", y: 1.08, x: 0.5, xanchor: "center" },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: "100%" }}
      useResizeHandler
    />
  );
}
