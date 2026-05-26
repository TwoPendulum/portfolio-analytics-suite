"use client";

import { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import TabNav from "@/components/TabNav";
import Overview from "@/components/correlation/Overview";
import DebugView from "@/components/correlation/DebugView";
import ForwardTable from "@/components/frontier/ForwardTable";
import FrontierPlot from "@/components/frontier/FrontierPlot";
import WeightsBar from "@/components/frontier/WeightsBar";
import CustomPortfolio from "@/components/frontier/CustomPortfolio";
import MethodologyView from "@/components/methodology/MethodologyView";
import { AssetConfig, MatrixData, RhoSeries, ComputeResponse, FrontierResponse } from "@/lib/types";
import { fetchAssets, fetchCompute, fetchFrontier, addAsset, updateAsset } from "@/lib/api";

function today(): string { return new Date().toISOString().slice(0, 10); }
function yearsAgo(n: number): string {
  const d = new Date(); d.setFullYear(d.getFullYear() - n);
  return d.toISOString().slice(0, 10);
}

export default function Home() {
  // Sidebar
  const [assets, setAssets] = useState<AssetConfig[]>([]);
  const [selectedTickers, setSelectedTickers] = useState<string[]>([]);
  const [startDate, setStartDate] = useState(yearsAgo(5));
  const [endDate, setEndDate] = useState(today());
  const [Q, setQ] = useState(0.001);
  const [R, setR] = useState(0.5);

  // Computation
  const [loading, setLoading] = useState(false);
  const [computedOnce, setComputedOnce] = useState(false);
  const [latestMatrices, setLatestMatrices] = useState<Record<string, MatrixData> | null>(null);
  const [rhoSeries, setRhoSeries] = useState<RhoSeries | null>(null);
  const [obsSeries, setObsSeries] = useState<RhoSeries | null>(null);
  const [activeTickers, setActiveTickers] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [historical, setHistorical] = useState<Record<string, { mu: number; sigma: number }>>({});

  // UI
  const [activeTab, setActiveTab] = useState("correlation");
  const [correlationSubtab, setCorrelationSubtab] = useState<"matrix" | "timeseries">("matrix");
  const [selectedHeatmapPair, setSelectedHeatmapPair] = useState<string | null>(null);

  // Frontier
  const [forwardRows, setForwardRows] = useState<{
    ticker: string; name: string; include: boolean; mu: number; sigma: number; allowShort: boolean;
  }[]>([]);
  const [rfRate, setRfRate] = useState(4.5);
  const [efResult, setEfResult] = useState<FrontierResponse | null>(null);
  const [efRhoMat, setEfRhoMat] = useState<number[][] | null>(null);
  const [efSigmas, setEfSigmas] = useState<number[] | null>(null);
  const [frontierPointIdx, setFrontierPointIdx] = useState(0);
  const [customPortfolio, setCustomPortfolio] = useState<{
    ret: number; vol: number; sharpe: number; tickers: string[];
  } | null>(null);

  useEffect(() => {
    fetchAssets().then((a: AssetConfig[]) => {
      setAssets(a);
      setSelectedTickers(a.map((x) => x.ticker));
    });
  }, []);

  const handleRun = useCallback(async () => {
    if (selectedTickers.length < 2) return;
    setLoading(true);
    try {
      const data: ComputeResponse = await fetchCompute({
        tickers: selectedTickers, startDate, endDate, Q, R,
      });
      setLatestMatrices(data.latestMatrices);
      setRhoSeries(data.rhoSeries);
      setObsSeries(data.obsSeries || {});
      setActiveTickers(data.activeTickers);
      setWarnings(data.warnings);
      setHistorical(data.historical || {});
      setComputedOnce(true);
      setEfResult(null);
      setEfRhoMat(null);
      setEfSigmas(null);
      setCustomPortfolio(null);
    } catch (e: any) {
      setWarnings([`Computation failed: ${e.message}`]);
    } finally {
      setLoading(false);
    }
  }, [selectedTickers, startDate, endDate, Q, R]);

  const handleAddAsset = useCallback(async (ticker: string, name: string, group: string) => {
    try {
      const result = await addAsset(ticker, name, group);
      if (result.warning) {
        setWarnings([result.warning]);
      }
      setAssets(result.assets);
      setSelectedTickers((prev) => [...prev, ticker]);
    } catch (e: any) {
      setWarnings([`Failed to add asset: ${e.message}`]);
    }
  }, []);

  const handleUpdateAsset = useCallback(async (ticker: string, name: string, group: string) => {
    try {
      const result = await updateAsset(ticker, name, group);
      if (result.error) {
        setWarnings([result.error]);
      }
      setAssets(result.assets);
    } catch (e: any) {
      setWarnings([`Failed to update asset: ${e.message}`]);
    }
  }, []);

  const handleAutoFill = () => {
    if (!activeTickers.length) return;
    const rows = activeTickers.map((t) => ({
      ticker: t,
      name: namesMap[t] || t,
      include: true,
      mu: historical[t]?.mu ?? 0,
      sigma: historical[t]?.sigma ?? 20,
      allowShort: false,
    }));
    setForwardRows(rows);
  };

  const handleComputeFrontier = async () => {
    const included = forwardRows.filter((r) => r.include);
    if (included.length < 2) return;
    const monthly = latestMatrices?.["monthly"];
    if (!monthly) return;

    const tickers = included.map((r) => r.ticker);
    const idxMap: Record<string, number> = {};
    monthly.tickers.forEach((t, i) => { idxMap[t] = i; });
    const n = tickers.length;
    const rhoMat: number[][] = Array.from({ length: n }, () => Array(n).fill(0));
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        const mi = idxMap[tickers[i]] ?? i;
        const mj = idxMap[tickers[j]] ?? j;
        rhoMat[i][j] = monthly.values[mi]?.[mj] ?? (i === j ? 1 : 0);
      }
    }
    try {
      const data: FrontierResponse = await fetchFrontier({
        tickers,
        mu: included.map((r) => r.mu / 100),
        sigma: included.map((r) => r.sigma / 100),
        monthlyRhoMatrix: rhoMat,
        rf: rfRate / 100,
        allowShort: included.some((r) => r.allowShort),
      });
      setEfResult(data);
      setEfRhoMat(rhoMat);
      setEfSigmas(included.map((r) => r.sigma / 100));
      setFrontierPointIdx(0);
      setWarnings(data.warnings || []);
    } catch (e: any) {
      setWarnings([`Frontier computation failed: ${e.message}`]);
    }
  };

  const frequencies = latestMatrices ? Object.keys(latestMatrices) : [];
  const namesMap: Record<string, string> = {};
  assets.forEach((a) => { namesMap[a.ticker] = a.name; });

  return (
    <div className="flex">
      <Sidebar
        assets={assets}
        selectedTickers={selectedTickers}
        startDate={startDate} endDate={endDate}
        Q={Q} R={R} loading={loading} computedOnce={computedOnce}
        activeTickers={activeTickers} frequencies={frequencies}
        onTickersChange={setSelectedTickers}
        onStartDateChange={setStartDate} onEndDateChange={setEndDate}
        onQChange={setQ} onRChange={setR} onRun={handleRun}
        onAddAsset={handleAddAsset}
        onUpdateAsset={handleUpdateAsset}
      />

      <main className="flex-1 p-6 space-y-6 min-w-0">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">Portfolio Analytics Suite</h1>
            <p className="text-gray-400">Dynamic correlation tracking & efficient frontier optimization</p>
          </div>
        </div>

        {warnings.length > 0 && (
          <div className="card border-yellow-600/40 bg-yellow-900/10 space-y-1">
            {warnings.map((w, i) => (
              <p key={i} className="text-sm text-yellow-400">{w}</p>
            ))}
          </div>
        )}

        {!computedOnce && (
          <div className="flex justify-center items-center h-64 text-gray-500">
            <p>Select assets and click <strong className="text-white">Run Computation</strong>.</p>
          </div>
        )}

        {computedOnce && (
          <>
            <TabNav active={activeTab} onChange={setActiveTab} />

            {/* ══════ Dynamic Correlation Tracking ══════ */}
            {activeTab === "correlation" && (
              <div className="space-y-4">
                {/* Sub-tabs */}
                <div className="flex space-x-1 border-b border-border/50">
                  <button
                    onClick={() => setCorrelationSubtab("matrix")}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                      correlationSubtab === "matrix"
                        ? "border-accent text-accent"
                        : "border-transparent text-gray-400 hover:text-gray-300"
                    }`}
                  >
                    Correlation Matrix
                  </button>
                  <button
                    onClick={() => setCorrelationSubtab("timeseries")}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                      correlationSubtab === "timeseries"
                        ? "border-accent text-accent"
                        : "border-transparent text-gray-400 hover:text-gray-300"
                    }`}
                  >
                    Time Series
                  </button>
                </div>

                {correlationSubtab === "matrix" && latestMatrices && (
                  <Overview
                    matrices={latestMatrices}
                    onCellClick={(pair) => {
                      setSelectedHeatmapPair(pair);
                      setCorrelationSubtab("timeseries");
                    }}
                  />
                )}
                {correlationSubtab === "timeseries" && rhoSeries && (
                  <DebugView
                    rhoSeries={rhoSeries}
                    obsSeries={obsSeries}
                    activeTickers={activeTickers}
                    initialPair={selectedHeatmapPair}
                  />
                )}
              </div>
            )}

            {/* ══════ Efficient Frontier ══════ */}
            {activeTab === "frontier" && (
              <div className="space-y-6">
                <ForwardTable
                  rows={forwardRows.length > 0 ? forwardRows : activeTickers.map((t) => ({
                    ticker: t, name: namesMap[t] || t, include: true,
                    mu: 0, sigma: 20, allowShort: false,
                  }))}
                  rfRate={rfRate}
                  onRowsChange={setForwardRows}
                  onRfChange={setRfRate}
                  onAutoFill={handleAutoFill}
                  onCompute={handleComputeFrontier}
                  excludedCount={forwardRows.filter((r) => !r.include).length}
                />

                {efResult && (
                  <>
                    <CustomPortfolio
                      tickers={efResult.assetPoints.tickers}
                      names={efResult.assetPoints.tickers.map((t: string) => namesMap[t] || t)}
                      onPlot={(weights) => {
                        const tickers = efResult.assetPoints.tickers;
                        const n = tickers.length;
                        const wArr = tickers.map((t: string) => (weights[t] || 0) / 100);
                        const ret = wArr.reduce((s, w, i) => s + w * efResult.assetPoints.ret[i], 0);
                        const sigmas = efResult.assetPoints.vol;
                        const rho = efRhoMat;
                        let variance = 0;
                        if (rho) {
                          for (let i = 0; i < n; i++) {
                            for (let j = 0; j < n; j++) {
                              const r = i === j ? 1.0 : Math.min(rho[i][j], 0.999);
                              variance += wArr[i] * wArr[j] * sigmas[i] * sigmas[j] * r;
                            }
                          }
                        } else {
                          variance = wArr.reduce((s, w, i) =>
                            s + w * w * sigmas[i] * sigmas[i], 0);
                        }
                        const vol = Math.sqrt(Math.max(variance, 0));
                        const sharpe = (ret - rfRate / 100) / (vol || 1e-10);
                        setCustomPortfolio({ ret, vol, sharpe, tickers });
                      }}
                    />

                    {customPortfolio && (
                      <div className="card">
                        <h4 className="text-sm font-medium text-gray-300 mb-2">Your Custom Portfolio</h4>
                        <div className="grid grid-cols-3 gap-4">
                          <div className="text-center">
                            <p className="text-xs text-gray-400">Expected Return</p>
                            <p className="text-lg font-bold text-white">{(customPortfolio.ret * 100).toFixed(2)}%</p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-gray-400">Volatility</p>
                            <p className="text-lg font-bold text-white">{(customPortfolio.vol * 100).toFixed(2)}%</p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-gray-400">Sharpe Ratio</p>
                            <p className="text-lg font-bold text-accent">{customPortfolio.sharpe.toFixed(3)}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    <FrontierPlot data={efResult} customPortfolio={customPortfolio} />

                    {efResult.efPoints.length > 0 && (
                      <div className="card">
                        <div className="flex items-center gap-4 mb-3">
                          <span className="text-sm text-gray-400">Frontier Point:</span>
                          <input
                            type="range" min={0} max={efResult.efPoints.length - 1}
                            value={frontierPointIdx}
                            onChange={(e) => setFrontierPointIdx(parseInt(e.target.value))}
                            className="flex-1 accent-accent"
                          />
                          <span className="text-sm font-mono text-white">
                            {frontierPointIdx + 1}/{efResult.efPoints.length}
                          </span>
                        </div>
                        {efResult.efPoints[frontierPointIdx] && (
                          <>
                            <p className="text-sm text-gray-400 mb-3">
                              Vol: {(efResult.efPoints[frontierPointIdx].vol * 100).toFixed(2)}% |
                              Ret: {(efResult.efPoints[frontierPointIdx].ret * 100).toFixed(2)}% |
                              Sharpe: {efResult.efPoints[frontierPointIdx].sharpe.toFixed(3)}
                            </p>
                            <WeightsBar
                              weights={efResult.efPoints[frontierPointIdx].weights}
                              tickers={efResult.assetPoints.tickers}
                            />
                          </>
                        )}
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-4">
                      {efResult.maxSharpe && (
                        <div className="card">
                          <h4 className="text-sm font-medium text-gray-300 mb-2">Max Sharpe Portfolio</h4>
                          <WeightsBar weights={efResult.maxSharpe.weights} tickers={efResult.assetPoints.tickers} />
                        </div>
                      )}
                      {efResult.minVol && (
                        <div className="card">
                          <h4 className="text-sm font-medium text-gray-300 mb-2">Min Vol Portfolio</h4>
                          <WeightsBar weights={efResult.minVol.weights} tickers={efResult.assetPoints.tickers} />
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            )}

            {/* ══════ Methodology ══════ */}
            {activeTab === "methodology" && <MethodologyView />}
          </>
        )}
      </main>
    </div>
  );
}
