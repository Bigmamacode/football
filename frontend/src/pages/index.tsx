import React from "react";
import MatchCard from "../components/MatchCard";
import { fetchPredictions } from "../lib/api";

export default function Home() {
  const [data, setData] = React.useState<any[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);

  React.useEffect(() => {
    fetchPredictions()
      .then(setData)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main style={{maxWidth:900, margin:"0 auto", display:"grid", gap:16}}>
      <h1 style={{fontSize:28, fontWeight:800}}>Probabilit\u00E0 Under/Over 2.5</h1>
      <p style={{color:"#6b7280"}}>MVP con modello Poisson su dati mock. Collega le API reali in <code>backend/data/loader.py</code>.</p>
      {loading && <div>Caricamento\u2026</div>}
      {error && <div style={{color:"crimson"}}>Errore: {error}</div>}
      <div style={{display:"grid", gap:12}}>
        {data.map((m, i) => (<MatchCard key={i} {...m} />))}
      </div>
    </main>
  );
}