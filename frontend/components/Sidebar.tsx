"use client";

import { useState } from "react";
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
  onAddAsset: (ticker: string, name: string, group: string) => void;
  onUpdateAsset: (ticker: string, name: string, group: string) => void;
}

export default function Sidebar(props: SidebarProps) {
  const {
    assets, selectedTickers,
    startDate, endDate, Q, R, loading, computedOnce,
    activeTickers, frequencies,
    onTickersChange, onStartDateChange, onEndDateChange,
    onQChange, onRChange, onRun, onAddAsset, onUpdateAsset,
  } = props;

  const [customTicker, setCustomTicker] = useState("");
  const [customName, setCustomName] = useState("");
  const [customGroup, setCustomGroup] = useState("");
  const [editingTicker, setEditingTicker] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editGroup, setEditGroup] = useState("");
  const allTickers = assets.map((a) => a.ticker);
  const duplicate = allTickers.includes(customTicker.toUpperCase());

  const handleAdd = () => {
    const ticker = customTicker.trim().toUpperCase();
    if (!ticker || duplicate) return;
    onAddAsset(ticker, customName.trim() || ticker, customGroup.trim() || "Custom");
    setCustomTicker("");
    setCustomName("");
    setCustomGroup("");
  };

  const startEdit = (a: AssetConfig) => {
    setEditingTicker(a.ticker);
    setEditName(a.name);
    setEditGroup(a.group);
  };

  const cancelEdit = () => {
    setEditingTicker(null);
    setEditName("");
    setEditGroup("");
  };

  const saveEdit = () => {
    if (editingTicker) {
      onUpdateAsset(editingTicker, editName.trim() || editingTicker, editGroup.trim() || "Custom");
    }
    cancelEdit();
  };

  return (
    <aside className="w-80 shrink-0 space-y-5 p-4 border-r border-border min-h-screen">
      <h2 className="text-lg font-bold text-white">Portfolio Analytics</h2>
      <hr className="border-border" />

      {/* Assets */}
      <div>
        <label className="text-sm text-gray-400 mb-2 block">Select Assets</label>
        <div className="max-h-80 overflow-y-auto space-y-1.5">
          {assets.map((a) => (
            <div key={a.ticker}>
              <div className="flex items-start gap-1 text-sm py-0.5 group">
                <label className="flex items-start gap-2 cursor-pointer flex-1 min-w-0">
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
                <button
                  onClick={() => startEdit(a)}
                  className="text-gray-600 hover:text-gray-400 shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Edit name / group"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                  </svg>
                </button>
              </div>
              {editingTicker === a.ticker && (
                <div className="ml-6 mt-1 mb-2 space-y-1.5">
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter") saveEdit(); if (e.key === "Escape") cancelEdit(); }}
                    placeholder="Name"
                    className="w-full text-xs px-2 py-1 rounded bg-surface border border-accent/50 text-white"
                  />
                  <input
                    type="text"
                    value={editGroup}
                    onChange={(e) => setEditGroup(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter") saveEdit(); if (e.key === "Escape") cancelEdit(); }}
                    placeholder="Group"
                    className="w-full text-xs px-2 py-1 rounded bg-surface border border-accent/50 text-white"
                  />
                  <div className="flex gap-1.5">
                    <button
                      onClick={saveEdit}
                      className="px-2 py-0.5 text-xs rounded bg-accent text-white font-medium"
                    >
                      Save
                    </button>
                    <button
                      onClick={cancelEdit}
                      className="px-2 py-0.5 text-xs rounded bg-surface border border-border text-gray-400"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Add Custom Ticker */}
      <div>
        <label className="text-xs text-gray-400 mb-1.5 block">Add Custom Ticker</label>
        <div className="space-y-1.5">
          <input
            type="text"
            value={customTicker}
            onChange={(e) => setCustomTicker(e.target.value.toUpperCase())}
            onKeyDown={(e) => { if (e.key === "Enter") handleAdd(); }}
            placeholder="Ticker (e.g. AAPL)"
            className="w-full text-sm px-2 py-1 rounded bg-surface border border-border text-white placeholder-gray-600"
          />
          <input
            type="text"
            value={customName}
            onChange={(e) => setCustomName(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleAdd(); }}
            placeholder="Name (optional)"
            className="w-full text-sm px-2 py-1 rounded bg-surface border border-border text-white placeholder-gray-600"
          />
          <div className="flex gap-1.5">
            <input
              type="text"
              value={customGroup}
              onChange={(e) => setCustomGroup(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleAdd(); }}
              placeholder="Group (optional)"
              className="flex-1 text-sm px-2 py-1 rounded bg-surface border border-border text-white placeholder-gray-600"
            />
            <button
              className="px-3 py-1 text-sm rounded bg-accent text-white font-medium disabled:opacity-40 shrink-0"
              disabled={!customTicker.trim() || duplicate}
              onClick={handleAdd}
            >
              Add
            </button>
          </div>
        </div>
        {duplicate && (
          <p className="text-xs text-yellow-400 mt-1">Ticker already exists.</p>
        )}
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
