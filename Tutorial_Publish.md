# 🚀 Tutorial Publish Aplikasi Aspiralytica

---

menjalankan backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

## 📋 Ada 2 Cara Publish

| Cara | Hasil | Cocok untuk |
|---|---|---|
| **Expo Go (sharing link)** | Link yang bisa dibuka di Expo Go app | Testing / demo ke dosen |
| **Build APK (file .apk)** | File APK yang bisa diinstall di Android | Distribusi nyata |

---

## 🅰️ CARA 1 — Share via Expo Go (Paling Cepat)

Cocok untuk **demo ke dosen atau teman** tanpa perlu build APK.

### Langkah:

```powershell
# 1. Login ke akun Expo (buat akun gratis di expo.dev)
npx expo login

# 2. Publish project ke Expo cloud
npx expo publish
```

Setelah selesai, kamu akan dapat link seperti:
```
https://expo.dev/@username/aspiralytica
```

Teman/dosen tinggal:
1. Install **Expo Go** dari Play Store
2. Buka link tersebut, atau scan QR code

⚠️ **Catatan**: Backend FastAPI tetap harus berjalan dan bisa diakses dari internet (lihat bagian Deploy Backend di bawah).

---

## 🅱️ CARA 2 — Build APK Android (File .apk)

### Step 1 — Install EAS CLI

```powershell
npm install -g eas-cli
eas login
```

### Step 2 — Inisialisasi EAS di project

```powershell
cd frontend
eas init
```

Pilih opsi **"Create a new EAS project"** jika diminta.

### Step 3 — Buat file `eas.json`

Buat file `frontend/eas.json` dengan isi:

```json
{
  "cli": {
    "version": ">= 5.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "android": {
        "buildType": "apk"
      },
      "distribution": "internal"
    },
    "production": {
      "android": {
        "buildType": "app-bundle"
      }
    }
  }
}
```

### Step 4 — Build APK

```powershell
# Build APK untuk testing (gratis, diproses di cloud Expo)
eas build --platform android --profile preview
```

Proses build memakan waktu **5-15 menit** di server Expo (gratis).
Setelah selesai, kamu akan dapat link download `.apk`.

### Step 5 — Download & Install APK

1. Buka link yang diberikan di browser HP
2. Download file `.apk`
3. Install (aktifkan "Install dari sumber tidak dikenal" di pengaturan HP)

---

## 🌐 Deploy Backend (Wajib untuk Publish)

Saat publish, `localhost` tidak lagi bisa dipakai. Backend harus bisa diakses dari internet.

### Opsi A — Railway (Gratis, Paling Mudah)

```bash
# 1. Buat akun di railway.app

# 2. Install Railway CLI
npm install -g @railway/cli

# 3. Login
railway login

# 4. Masuk ke folder backend
cd backend

# 5. Buat file Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port $PORT" > Procfile

# 6. Deploy
railway init
railway up
```

Setelah deploy, Railway akan memberi URL seperti:
```
https://aspiralytica-backend.up.railway.app
```

### Opsi B — Render.com (Gratis, Alternatif)

1. Buat akun di **render.com**
2. New → Web Service → Connect GitHub repo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Klik **Deploy**

---

## 🔗 Update BASE_URL Setelah Deploy

Setelah backend ter-deploy, update `frontend/src/api/api.ts` dan `auth.ts`:

```typescript
// Ganti ini:
const BASE_URL = 'http://192.168.1.7:8000';

// Menjadi URL Railway/Render kamu:
const BASE_URL = 'https://aspiralytica-backend.up.railway.app';
```

Lalu build ulang APK:
```powershell
eas build --platform android --profile preview
```

---

## ✅ Checklist Sebelum Publish

- [ ] Semua screen berfungsi tanpa error
- [ ] Backend sudah di-deploy ke Railway/Render
- [ ] `BASE_URL` di `api.ts` dan `auth.ts` sudah diupdate ke URL production
- [ ] `app.json` sudah diisi nama, slug, dan icon yang benar
- [ ] Test login, daftar, analisis laporan, riwayat dari HP
- [ ] `eas.json` sudah dibuat

---

## 📱 Untuk Sidang / Demo ke Dosen

Cara paling simpel tanpa ribet deploy:

1. **Jalankan backend di laptop**
2. **Sambungkan HP ke WiFi yang sama dengan laptop**
3. **Jalankan** `npx expo start`
4. **Scan QR** dengan Expo Go

Ini sudah cukup untuk demo langsung tanpa perlu publish ke internet sama sekali.
