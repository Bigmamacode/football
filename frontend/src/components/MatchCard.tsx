import React from "react";

type Props = {
  home: string;
  away: string;
  league: string;
  kickoff: string;
  lambda_home: number;
  lambda_away: number;
  under25: number;
  over25: number;
};

export default function MatchCard(p: Props) {
  const toPercent = (x: number) => `${(x * 100).toFixed(1)}%`;
  return (
    <div style={{border:"1px solid #e5e7eb", borderRadius:12, padding:16, display:"grid", gap:8}}>
      <div style={{fontSize:14, color:"#6b7280"}}>{p.league} • {new Date(p.kickoff).toLocaleString()}</div>
      <div style={{fontSize:18, fontWeight:700}}>{p.home} vs {p.away}</div>
      <div style={{display:"flex", gap:16, fontSize:14}}>
        <div>λ Home: <b>{p.lambda_home}</b></div>
        <div>λ Away: <b>{p.lambda_away}</b></div>
      </div>
      <div style={{display:"flex", gap:16, alignItems:"center"}}>
        <div>Under 2.5: <b>{toPercent(p.under25)}</b></div>
        <div>Over 2.5: <b>{toPercent(p.over25)}</b></div>
      </div>
    </div>
  );
}
