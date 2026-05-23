"use client";

import PlotlyHeatmap from "./PlotlyHeatmap";
import { MatrixData } from "@/lib/types";

interface Props {
  freqKey: string;
  label: string;
  matrix: MatrixData;
  onCellClick?: (pair: string) => void;
}

export default function HeatmapCard({ freqKey, label, matrix, onCellClick }: Props) {
  return (
    <div className="card">
      <div style={{ minHeight: 500 }}>
        <PlotlyHeatmap matrix={matrix} title={label} onCellClick={onCellClick} />
      </div>
    </div>
  );
}
