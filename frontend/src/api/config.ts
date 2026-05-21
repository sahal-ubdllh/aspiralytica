// frontend/src/api/config.ts
// ─────────────────────────────────────────────────
// Ganti BASE_URL sesuai situasi jaringan kamu.
// Cukup edit FILE INI SAJA, api.ts & auth.ts
// tidak perlu disentuh lagi.
// ─────────────────────────────────────────────────
 
// ── OPSI 1: WiFi yang sama (development di rumah/kampus) ──
// Cek IP laptop: ipconfig (Windows) → cari IPv4
// const BASE_URL = 'http://192.168.1.7:8000';
 
// ── OPSI 2: Hotspot dari HP ──────────────────────────────
// Laptop konek ke hotspot HP, cek IP laptop di ipconfig
// const BASE_URL = 'http://192.168.43.105:8000';
 
// ── OPSI 3: ngrok (dari mana saja, laptop harus nyala) ───
// Jalankan: ngrok http 8000 → copy URL yang muncul
// const BASE_URL = 'https://abc123.ngrok-free.app';
 
// ── OPSI 4: Railway / server production ──────────────────
// const BASE_URL = 'https://aspiralytica-backend.up.railway.app';
 
// ↓↓↓ AKTIFKAN SATU BARIS INI, SISANYA TETAP COMMENT ↓↓↓
export const BASE_URL = 'http://192.168.1.7:8000';