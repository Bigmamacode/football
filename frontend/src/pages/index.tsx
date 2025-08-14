import React from "react";
import { fetchPredictions, type UIPrediction, API_BASE } from "../lib/api";
import MatchCard from "../components/MatchCard";

export default function HomePage() {
  const [items, setItems] = React.useState<UIPrediction[] | null>(null);
  const [err, setErr] = React.useState<string | null>(null);

  React.useEffect(() => {
    (async () => {
      try {
        const data = await fetchPredictions({ forceMock: false });
        setItems(data);
      } catch (e: any) {
        setErr(String(e?.message || e));
      }
    })();
  }, []);

  return (
    <main style={{maxWidth: 840, margin: "40px auto", padding: "0 16px", fontFamily: "system-ui"}}>
      <h1 style={{marginBottom: 4}}>Probabilità Under/Over 2.5</h1>
      <div style={{opacity:0.7, marginBottom:16}}>
        API: <code>{API_BASE}</code>
      </div>
      {err && <div style={{color:"crimson", marginBottom:12}}>Errore: {err}</div>}
      {!items && !err && <div>Caricamento…</div>}
      {items && items.length === 0 && <div>Nessuna partita trovata.</div>}
      <div style={{display:"grid", gap:12}}>
        {items?.map((p, i) => <MatchCard key={i} p={p} />)}
      </div>
    </main>
  );
}