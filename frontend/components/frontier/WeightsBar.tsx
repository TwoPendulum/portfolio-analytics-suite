"use client";

import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface Props {
  weights: number[];
  tickers: string[];
}

export default function WeightsBar({ weights, tickers }: Props) {
  const colors = weights.map((w) => (w >= 0 ? "#4A90D9" : "#B22222"));

  return (
    <Plot
      data={[
        {
          type: "bar",
          x: weights,
          y: tickers,
          orientation: "h",
          marker: { color: colors },
          text: weights.map((w) => `${(w * 100).toFixed(1)}%`),
          textposition: "outside",
          hovertemplate: "%{y}: %{x:.2%}<extra></extra>",
        } as any,
      ]}
      layout={{
        template: "plotly_dark",
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: "#E0E0E0" },
        height: Math.max(200, tickers.length * 28 + 50),
        xaxis: { title: "Weight", tickformat: ".0%", gridcolor: "#2D2D44", automargin: true },
        yaxis: { autorange: "reversed", automargin: true },
        margin: { l: 80, r: 50, t: 10, b: 40 },
        showlegend: false,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%" }}
      useResizeHandler
    />
  );
}
