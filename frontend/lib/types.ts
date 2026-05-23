export interface AssetConfig {
  ticker: string;
  name: string;
  group: string;
}

export interface MatrixData {
  tickers: string[];
  values: number[][];
}

export interface SeriesData {
  dates: string[];
  values: number[];
}

export interface RhoSeries {
  [freq: string]: {
    [pairKey: string]: SeriesData;
  };
}

export interface ComputeResponse {
  latestMatrices: Record<string, MatrixData>;
  rhoSeries: RhoSeries;
  obsSeries: RhoSeries;
  activeTickers: string[];
  warnings: string[];
  historical: Record<string, { mu: number; sigma: number }>;
}

export interface PortfolioPoint {
  weights: number[];
  ret: number;
  vol: number;
  sharpe: number;
}

export interface AssetPoint {
  tickers: string[];
  vol: number[];
  ret: number[];
}

export interface FrontierResponse {
  efPoints: PortfolioPoint[];
  maxSharpe: PortfolioPoint | null;
  minVol: PortfolioPoint | null;
  assetPoints: AssetPoint;
  warnings: string[];
}

export interface AppState {
  // Computation results
  latestMatrices: Record<string, MatrixData> | null;
  rhoSeries: RhoSeries | null;
  activeTickers: string[];
  warnings: string[];
  loading: boolean;

  // Tab 1
  selectedHeatmapPair: string | null; // "TICKER_A|TICKER_B"

  // Tab 2
  forwardMu: Record<string, number>;
  forwardSigma: Record<string, number>;
  includeAsset: Record<string, boolean>;
  allowShort: Record<string, boolean>;
  rfRate: number;
  efResult: FrontierResponse | null;
  customPortfolio: { weights: Record<string, number>; ret: number; vol: number; sharpe: number } | null;

  // Tab 3
  language: "zh" | "en";

  // Sidebar
  assets: AssetConfig[];
  selectedTickers: string[];
  startDate: string;
  endDate: string;
  Q: number;
  R: number;
}
