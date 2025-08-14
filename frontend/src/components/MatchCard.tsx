import React from "react";
import type { UIPrediction } from "../lib/api";

function pct(x: number | undefined | null): string {
  const n = typeof x === "number" ? x : NaN;
  return Number.isFinite(n) ? `${Math.round(n * 100)}%` : "—";
}

function num(x: number | undefined | null, d=3): string {
  const n = typeof x === "number" ? x : NaN;
  return Number.isFinite(n) ? n.toFixed(d) : "—";
}

export default function MatchCard({ p }: { p: UIPrediction }) {
  return (
    <div style={{
      border: "1px solid #e5e7eb", borderRadius: 12, padding: 16,
      display: "grid", gap: 8, fontFamily: "system-ui"
    }}>
      <div style={{fontWeight:700}}>{p.home} vs {p.away}</div>
      <div style={{opacity:0.8}}>
        &lambda; Home: <strong>{num(p.lambdaHome)}</strong> ·
        &nbsp;&lambda; Away: <strong>{num(p.lambdaAway)}</strong>
      </div>
      <div>Linea: <code>{p.line}</code></div>
      <div style={{display:"flex", gap:12}}>
        <span>Under {p.line}: <strong>{pct(p.pUnder)}</strong></span>
        <span>Over {p.line}: <strong>{pct(p.pOver)}</strong></span>
      </div>
    </div>
  );
}