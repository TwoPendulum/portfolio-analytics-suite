"use client";

import { useState, useMemo } from "react";
import PlotlyTimeseries from "./PlotlyTimeseries";
import { RhoSeries } from "@/lib/types";

interface Props {
  rhoSeries: RhoSeries;
  obsSeries: RhoSeries | null;
  activeTickers: string[];
  initialPair: string | null;
}

function generatePairs(tickers: string[]): { key: string; label: string }[] {
  const pairs: { key: string; label: string }[] = [];
  for (let i = 0; i < tickers.length; i++) {
    for (let j = i + 1; j < tickers.length; j++) {
      const a = tickers[i];
      const b = tickers[j];
      // Sort alphabetically to match backend serialization
      const key = a < b ? `${a}|${b}` : `${b}|${a}`;
      pairs.push({ key, label: `${a} vs ${b}` });
    }
  }
  return pairs;
}

export default function DebugView({ rhoSeries, obsSeries, activeTickers, initialPair }: Props) {
  const allPairs = useMemo(() => generatePairs(activeTickers), [activeTickers]);
  const [selected, setSelected] = useState<string[]>(initialPair ? [initialPair] : []);

  const togglePair = (key: string) => {
    setSelected((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  };

  return (
    <div className="space-y-6">
      {/* Pair selector */}
      <div className="card">
        <h3 className="text-sm font-medium text-gray-300 mb-3">Select Pairs (multi-select)</h3>
        <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
          {allPairs.map((p) => {
            const active = selected.includes(p.key);
            return (
              <button
                key={p.key}
                onClick={() => togglePair(p.key)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${
                  active
                    ? "bg-accent text-white"
                    : "bg-surface border border-border text-gray-400 hover:border-accent"
                }`}
              >
                {p.label}
              </button>
            );
          })}
        </div>
        {selected.length > 0 && (
          <p className="text-xs text-gray-500 mt-2">{selected.length} pair(s) selected</p>
        )}
      </div>

      {/* Timeseries charts */}
      {selected.length === 0 && (
        <p className="text-gray-400">Select one or more asset pairs above to view time series.</p>
      )}

      <div className="space-y-6">
        {selected.map((pairKey) => {
          const [a, b] = pairKey.split("|");

          // Collect rho data across frequencies for this pair
          const chartData: Record<string, { x: string[]; y: number[] }> = {};
          const chartObs: Record<string, { x: string[]; y: number[] }> = {};

          for (const freq of ["daily", "weekly", "monthly"]) {
            const freqData = rhoSeries[freq];
            if (!freqData) continue;

            const series = freqData[pairKey];
            if (series) {
              chartData[freq] = {
                x: series.dates,
                y: series.values,
              };
            }

            // Obs data
            const obsFreq = obsSeries?.[freq];
            if (obsFreq) {
              const obs = obsFreq[pairKey];
              if (obs) {
                chartObs[freq] = {
                  x: obs.dates,
                  y: obs.values,
                };
              }
            }
          }

          return (
            <div key={pairKey} className="card">
              <h3 className="text-sm font-medium text-white mb-2">{a} vs {b}</h3>
              <PlotlyTimeseries
                data={chartData}
                obsData={chartObs}
                pairLabel={`${a} vs ${b}`}
              />
              {/* Latest values */}
              <div className="grid grid-cols-3 gap-4 mt-3">
                {["daily", "weekly", "monthly"].map((freq) => {
                  const s = chartData[freq];
                  if (!s || s.y.length === 0) return null;
                  const latest = s.y[s.y.length - 1];
                  const prev = s.y.length > 22 ? s.y[s.y.length - 23] : s.y[0];
                  const delta = latest - prev;
                  return (
                    <div key={freq} className="text-center">
                      <p className="text-xs text-gray-400">{freq.charAt(0).toUpperCase() + freq.slice(1)}</p>
                      <p className="text-lg font-bold text-white">{(latest * 100).toFixed(1)}%</p>
                      <p className={`text-xs ${delta >= 0 ? "text-green-400" : "text-red-400"}`}>
                        {delta >= 0 ? "+" : ""}{(delta * 100).toFixed(1)}% (1M)
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
