"use client";

import HeatmapCard from "./HeatmapCard";
import { MatrixData } from "@/lib/types";

interface Props {
  matrices: Record<string, MatrixData>;
  onCellClick?: (pair: string) => void;
}

const FREQ_LABELS: Record<string, string> = {
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
};

export default function Overview({ matrices, onCellClick }: Props) {
  const freqs = ["daily", "weekly", "monthly"].filter((f) => matrices[f]);

  if (freqs.length === 0) {
    return <p className="text-gray-400">No matrix data available.</p>;
  }

  return (
    <div className="flex flex-col gap-6">
      {freqs.map((freq) => (
        <HeatmapCard
          key={freq}
          freqKey={freq}
          label={FREQ_LABELS[freq] || freq}
          matrix={matrices[freq]}
          onCellClick={onCellClick}
        />
      ))}
    </div>
  );
}
