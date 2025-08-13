export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
export async function fetchPredictions() {
  const res = await fetch(`${API_BASE}/predictions`);
  if (!res.ok) throw new Error("API error");
  return res.json();
}
