"use client";

import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface Props {
  data: Record<string, { x: string[]; y: number[] }>;
  obsData: Record<string, { x: string[]; y: number[] }>;
  pairLabel: string;
}

const FREQ_COLORS: Record<string, string> = {
  daily: "#4A90D9",
  weekly: "#50C878",
  monthly: "#FFA500",
};

const FREQ_WIDTH: Record<string, number> = { daily: 2, weekly: 1.5, monthly: 1.5 };
const FREQ_DASH: Record<string, string> = { daily: "solid", weekly: "solid", monthly: "dash" };

export default function PlotlyTimeseries({ data, obsData, pairLabel }: Props) {
  const traces: any[] = [];

  // Reference lines
  traces.push({
    type: "scatter",
    x: [data.daily?.x[0] || "", data.daily?.x[data.daily.x.length - 1] || ""],
    y: [1, 1],
    mode: "lines",
    name: "ρ = +1",
    line: { dash: "dash", color: "gray", width: 1 },
    opacity: 0.3,
    showlegend: false,
  });
  traces.push({
    type: "scatter",
    x: [data.daily?.x[0] || "", data.daily?.x[data.daily.x.length - 1] || ""],
    y: [-1, -1],
    mode: "lines",
    name: "ρ = -1",
    line: { dash: "dash", color: "gray", width: 1 },
    opacity: 0.3,
    showlegend: false,
  });

  // Rho curves
  const freqOrder = ["daily", "weekly", "monthly"];
  for (const freq of freqOrder) {
    const d = data[freq];
    if (!d) continue;
    traces.push({
      type: "scatter",
      x: d.x,
      y: d.y,
      mode: "lines",
      name: freq.charAt(0).toUpperCase() + freq.slice(1),
      line: {
        color: FREQ_COLORS[freq] || "#888",
        width: FREQ_WIDTH[freq] || 1.5,
        dash: FREQ_DASH[freq] || "solid",
      },
      hovertemplate: `${freq}: %{y:.3f}<br>%{x}<extra></extra>`,
    });
  }

  // Obs scatter
  for (const freq of freqOrder) {
    const o = obsData[freq];
    if (!o) continue;
    traces.push({
      type: "scatter",
      x: o.x,
      y: o.y,
      mode: "markers",
      name: `Obs (${freq})`,
      marker: { color: "gray", size: 2, opacity: 0.12 },
      showlegend: false,
      hovertemplate: `Obs: %{y:.3f}<br>%{x}<extra></extra>`,
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
        height: 350,
        hovermode: "x unified",
        legend: { orientation: "h", y: 1.12, x: 0.5, xanchor: "center" },
        margin: { l: 60, r: 20, t: 40, b: 50 },
        yaxis: { range: [-1.25, 1.25], title: "ρ", tickformat: ".0%", gridcolor: "#2D2D44", automargin: true },
        xaxis: { title: "", type: "date", gridcolor: "#2D2D44", automargin: true },
        title: { text: pairLabel, font: { size: 15, color: "#E0E0E0" } },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: "100%" }}
      useResizeHandler
    />
  );
}
