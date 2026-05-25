const API_BASE = "http://localhost:8000";

export async function fetchAssets() {
  const res = await fetch(`${API_BASE}/api/assets`);
  if (!res.ok) throw new Error("Failed to fetch assets");
  const data = await res.json();
  return data.assets;
}

export async function addAsset(ticker: string, name: string, group: string) {
  const res = await fetch(`${API_BASE}/api/assets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker, name, group }),
  });
  if (!res.ok) throw new Error("Failed to add asset");
  const data = await res.json();
  return { assets: data.assets, warning: data.warning };
}

export async function updateAsset(ticker: string, name: string, group: string) {
  const res = await fetch(`${API_BASE}/api/assets/${ticker}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, group }),
  });
  if (!res.ok) throw new Error("Failed to update asset");
  const data = await res.json();
  return { assets: data.assets, error: data.error };
}

export async function fetchCompute(params: {
  tickers: string[];
  startDate: string;
  endDate: string;
  Q: number;
  R: number;
}) {
  const res = await fetch(`${API_BASE}/api/compute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tickers: params.tickers,
      startDate: params.startDate,
      endDate: params.endDate,
      Q: params.Q,
      R: params.R,
    }),
  });
  if (!res.ok) throw new Error("Computation failed");
  return res.json();
}

export async function fetchFrontier(params: {
  tickers: string[];
  mu: number[];
  sigma: number[];
  monthlyRhoMatrix: number[][];
  rf: number;
  allowShort: boolean;
}) {
  const res = await fetch(`${API_BASE}/api/frontier`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tickers: params.tickers,
      mu: params.mu,
      sigma: params.sigma,
      monthlyRhoMatrix: params.monthlyRhoMatrix,
      rf: params.rf,
      allowShort: params.allowShort,
      nPoints: 100,
    }),
  });
  if (!res.ok) throw new Error("Frontier computation failed");
  return res.json();
}

export async function fetchMethodology(lang: string) {
  const res = await fetch(`${API_BASE}/api/methodology/${lang}`);
  if (!res.ok) throw new Error("Failed to fetch methodology");
  const data = await res.json();
  return data.content;
}
