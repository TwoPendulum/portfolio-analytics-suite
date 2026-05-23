"use client";

import { useState } from "react";

interface Props {
  tickers: string[];
  names: string[];
  onPlot: (weights: Record<string, number>) => void;
}

export default function CustomPortfolio({ tickers, names, onPlot }: Props) {
  const n = tickers.length;
  const [weights, setWeights] = useState<number[]>(() =>
    tickers.map(() => parseFloat((100 / n).toFixed(1)))
  );

  const total = weights.reduce((s, v) => s + v, 0);
  const isValid = Math.abs(total - 100) < 0.05;

  const setWeight = (idx: number, val: number) => {
    const next = [...weights];
    next[idx] = val;
    setWeights(next);
  };

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-300">Custom Portfolio</h3>
        <span className={`text-xs font-mono ${isValid ? "text-green-400" : "text-red-400"}`}>
          {isValid ? `Sum: ${total.toFixed(1)}%` : `Sum: ${total.toFixed(1)}% (need 100%)`}
        </span>
      </div>

      <div className="grid grid-cols-4 gap-1.5">
        {tickers.map((t, i) => (
          <div key={t}
            className="flex items-center justify-between bg-surface/50 rounded px-2 py-1 border border-border/50"
          >
            <span className="text-xs text-gray-300 truncate">
              <span className="font-mono text-white">{t}</span>
              <span className="text-gray-500 ml-1">{names[i] || ""}</span>
            </span>
            <span className="text-xs text-gray-300 shrink-0 ml-2 tabular-nums">
              <input
                type="number" step="0.1" min="-50" max="100"
                value={weights[i]}
                onChange={(e) => setWeight(i, parseFloat(e.target.value) || 0)}
                className="w-14 text-right text-xs bg-transparent outline-none text-white
                  [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              />%
            </span>
          </div>
        ))}
      </div>

      <button
        className="btn-primary text-sm w-full"
        disabled={!isValid}
        onClick={() => {
          const wts: Record<string, number> = {};
          tickers.forEach((t, i) => { wts[t] = weights[i]; });
          onPlot(wts);
        }}
      >
        Plot on Frontier
      </button>
    </div>
  );
}
