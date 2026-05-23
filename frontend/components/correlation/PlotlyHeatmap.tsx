"use client";

import dynamic from "next/dynamic";
import { MatrixData } from "@/lib/types";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface Props {
  matrix: MatrixData;
  title: string;
  onCellClick?: (pair: string) => void;
}

export default function PlotlyHeatmap({ matrix, title, onCellClick }: Props) {
  const { tickers, values } = matrix;
  const z = values;

  const colorscale: [number, string][] = [
    [0, "#B22222"],
    [0.25, "#E57373"],
    [0.5, "#FFFFFF"],
    [0.75, "#64B5F6"],
    [1, "#1E90FF"],
  ];

  return (
    <Plot
      data={[
        {
          type: "heatmap",
          z,
          x: tickers,
          y: tickers,
          zmin: -1,
          zmax: 1,
          colorscale,
          text: z.map((row) => row.map((v) => v.toFixed(2))),
          texttemplate: "%{text}",
          textfont: { color: "#333", size: 11 },
          hovertemplate: "%{x} vs %{y}<br>ρ = %{z:.3f}<extra></extra>",
          colorbar: {
            title: { text: "ρ", side: "right" },
            tickvals: [-1, -0.5, 0, 0.5, 1],
            ticktext: ["-1.0", "-0.5", "0.0", "0.5", "1.0"],
          },
        } as any,
      ]}
      layout={{
        template: "plotly_dark",
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: "#E0E0E0" },
        height: 480,
        xaxis: { side: "bottom", tickangle: -30, automargin: true },
        yaxis: { autorange: "reversed", automargin: true },
        margin: { l: 80, r: 10, t: 50, b: 60 },
        title: { text: title, font: { size: 16, color: "#E0E0E0" } },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: "100%" }}
      useResizeHandler
      onClick={(e: any) => {
        if (onCellClick && e.points && e.points.length > 0) {
          const pt = e.points[0];
          const a = tickers[pt.y];
          const b = tickers[pt.x];
          if (a !== b) {
            const pair = a < b ? `${a}|${b}` : `${b}|${a}`;
            onCellClick(pair);
          }
        }
      }}
    />
  );
}
