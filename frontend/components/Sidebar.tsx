"use client";

import { AssetConfig } from "@/lib/types";

interface SidebarProps {
  assets: AssetConfig[];
  selectedTickers: string[];
  startDate: string;
  endDate: string;
  Q: number;
  R: number;
  loading: boolean;
  computedOnce: boolean;
  activeTickers: string[];
  frequencies: string[];
  onTickersChange: (tickers: string[]) => void;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
  onQChange: (q: number) => void;
  onRChange: (r: number) => void;
  onRun: () => void;
}

export default function Sidebar(props: SidebarProps) {
  const {
    assets, selectedTickers,
    startDate, endDate, Q, R, loading, computedOnce,
    activeTickers, frequencies,
    onTickersChange, onStartDateChange, onEndDateChange,
    onQChange, onRChange, onRun,
  } = props;

  return (
    <aside className="w-80 shrink-0 space-y-5 p-4 border-r border-border min-h-screen">
      <h2 className="text-lg font-bold text-white">Portfolio Analytics</h2>
      <hr className="border-border" />

      {/* Assets */}
      <div>
        <label className="text-sm text-gray-400 mb-2 block">Select Assets</label>
        <div className="max-h-80 overflow-y-auto space-y-1.5">
          {assets.map((a) => (
            <label key={a.ticker} className="flex items-start gap-2 text-sm cursor-pointer py-0.5">
              <input
                type="checkbox"
                checked={selectedTickers.includes(a.ticker)}
                onChange={() => {
                  if (selectedTickers.includes(a.ticker)) {
                    onTickersChange(selectedTickers.filter((t) => t !== a.ticker));
                  } else {
                    onTickersChange([...selectedTickers, a.ticker]);
                  }
                }}
                className="accent-accent mt-0.5 shrink-0"
              />
              <div className="min-w-0">
                <span className="text-gray-300">{a.ticker} — {a.name}</span>
                <span className="text-gray-500 text-xs ml-2">{a.group}</span>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Date Range */}
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="text-xs text-gray-400">Start</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => onStartDateChange(e.target.value)}
            className="w-full text-sm"
          />
        </div>
        <div>
          <label className="text-xs text-gray-400">End</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => onEndDateChange(e.target.value)}
            className="w-full text-sm"
          />
        </div>
      </div>

      {/* Advanced */}
      <details className="text-sm">
        <summary className="text-gray-400 cursor-pointer">Advanced Parameters</summary>
        <div className="mt-2 space-y-3 pl-2">
          <div>
            <label className="text-xs text-gray-400">
              Q (process noise): <span className="text-white font-mono">{Q.toFixed(4)}</span>
            </label>
            <input
              type="range" min="0.0001" max="0.1" step="0.0001"
              value={Q}
              onChange={(e) => onQChange(parseFloat(e.target.value))}
              className="w-full accent-accent"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400">
              R (observation noise): <span className="text-white font-mono">{R.toFixed(2)}</span>
            </label>
            <input
              type="range" min="0.01" max="2.0" step="0.01"
              value={R}
              onChange={(e) => onRChange(parseFloat(e.target.value))}
              className="w-full accent-accent"
            />
          </div>
        </div>
      </details>

      <hr className="border-border" />

      {/* Run */}
      <button
        className="btn-primary w-full"
        disabled={loading || selectedTickers.length < 2}
        onClick={onRun}
      >
        {loading ? "Computing..." : "Run Computation"}
      </button>
      {selectedTickers.length < 2 && (
        <p className="text-xs text-gray-500">Select at least 2 assets.</p>
      )}

      {/* Status */}
      {computedOnce && (
        <div className="text-xs text-green-400 space-y-0.5">
          <p>Active: {activeTickers.length} assets</p>
          {frequencies.length > 0 && <p>Frequencies: {frequencies.join(", ")}</p>}
        </div>
      )}
    </aside>
  );
}
