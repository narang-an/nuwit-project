const API_BASE = "http://127.0.0.1:5001";

export async function getSavedOutfits() {
  const res = await fetch(`${API_BASE}/saved_outfits`);
  return res.json();
}