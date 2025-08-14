export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";

export type APIPrediction = {
  league?: string;
  home: string;
  away: string;
  kickoff?: string;
  lambda_home: number;
  lambda_away: number;
  line: number;
  p_under: number;
  p_over: number;
};

export type UIPrediction = {
  league?: string;
  home: string;
  away: string;
  kickoff?: string;
  lambdaHome: number;
  lambdaAway: number;
  line: number;
  pUnder: number;
  pOver: number;
};

export async function fetchPredictions(options?: { forceMock?: boolean }): Promise<UIPrediction[]> {
  const force = options?.forceMock ? "?force_mock=1" : "";
  if (!API_BASE) throw new Error("NEXT_PUBLIC_API_BASE non impostata");
  const url = `${API_BASE}/predictions${force}`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${res.status}`);
  const data: APIPrediction[] = await res.json();

  return (data || []).map((p) => ({
    league: p.league,
    home: p.home,
    away: p.away,
    kickoff: p.kickoff,
    lambdaHome: Number(p.lambda_home),
    lambdaAway: Number(p.lambda_away),
    line: Number(p.line ?? 2.5),
    pUnder: Number(p.p_under),
    pOver: Number(p.p_over),
  }));
}