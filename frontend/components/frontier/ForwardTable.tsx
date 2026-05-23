"use client";

interface AssetRow {
  ticker: string;
  name: string;
  include: boolean;
  mu: number;
  sigma: number;
  allowShort: boolean;
}

interface Props {
  rows: AssetRow[];
  rfRate: number;
  onRowsChange: (rows: AssetRow[]) => void;
  onRfChange: (rf: number) => void;
  onAutoFill: () => void;
  onCompute: () => void;
  excludedCount: number;
}

export default function ForwardTable({
  rows, rfRate, onRowsChange, onRfChange, onAutoFill, onCompute,
  excludedCount,
}: Props) {
  const updateRow = (idx: number, patch: Partial<AssetRow>) => {
    const next = [...rows];
    next[idx] = { ...next[idx], ...patch };
    onRowsChange(next);
  };

  const includedRows = rows.filter((r) => r.include);
  const canCompute = includedRows.length >= 2;

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-300">Forward Estimates</h3>
        <div className="flex items-center gap-4">
          <button onClick={onAutoFill} className="text-sm text-accent hover:text-accent-hover transition-colors">
            Auto-fill from History
          </button>
          <label className="flex items-center gap-2 text-sm text-gray-400">
            RF Rate (%):
            <input
              type="number" step="0.1" min="0" max="20"
              value={rfRate}
              onChange={(e) => onRfChange(parseFloat(e.target.value) || 0)}
              className="w-20 text-sm text-right"
            />
          </label>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-400 border-b border-border">
              <th className="py-2 pr-4 font-medium">Ticker</th>
              <th className="py-2 pr-4 font-medium">Name</th>
              <th className="py-2 pr-4 font-medium text-center">Include</th>
              <th className="py-2 pr-4 font-medium text-right">Forward μ (%)</th>
              <th className="py-2 pr-4 font-medium text-right">Forward σ (%)</th>
              <th className="py-2 font-medium text-center">Short</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr key={row.ticker} className="border-b border-border/30 hover:bg-surface/50">
                <td className="py-2 pr-4 font-mono text-white">{row.ticker}</td>
                <td className="py-2 pr-4 text-gray-400">{row.name}</td>
                <td className="py-2 pr-4 text-center">
                  <input
                    type="checkbox"
                    checked={row.include}
                    onChange={(e) => updateRow(idx, { include: e.target.checked })}
                    className="accent-accent"
                  />
                </td>
                <td className="py-2 pr-4 text-right">
                  <input
                    type="number" step="0.1"
                    value={row.mu}
                    onChange={(e) => updateRow(idx, { mu: parseFloat(e.target.value) || 0 })}
                    className="w-24 text-right text-white bg-transparent border border-border rounded px-2 py-1 focus:border-accent"
                  />
                </td>
                <td className="py-2 pr-4 text-right">
                  <input
                    type="number" step="0.1" min="0.1"
                    value={row.sigma}
                    onChange={(e) => updateRow(idx, { sigma: parseFloat(e.target.value) || 0.1 })}
                    className="w-24 text-right text-white bg-transparent border border-border rounded px-2 py-1 focus:border-accent"
                  />
                </td>
                <td className="py-2 text-center">
                  <input
                    type="checkbox"
                    checked={row.allowShort}
                    onChange={(e) => updateRow(idx, { allowShort: e.target.checked })}
                    className="accent-accent"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {excludedCount > 0 && (
        <p className="text-xs text-gray-500">{excludedCount} asset(s) excluded.</p>
      )}

      <button
        className="btn-primary"
        disabled={!canCompute}
        onClick={onCompute}
      >
        Compute Efficient Frontier
      </button>
      {!canCompute && (
        <p className="text-xs text-red-400">At least 2 assets must be included.</p>
      )}
    </div>
  );
}
