"""
══════════════════════════════════════════════════════════════════
SEEDER — Label: BAD
Uji pipeline TSC model xgb_model_A3 (Window=4)
══════════════════════════════════════════════════════════════════
Mengirim 4 data sensor berurutan (t-3 → t-0) untuk mensimulasikan
window klasifikasi Bad.

Range Bad:
  mq135       : 410 – 652  (dipakai: 460-520, mean=481)
  ppm_co      : 17  – 34   (dipakai: 20.10-24.50)
  ppm_nh3     : 1200– 1800 (dipakai: 1230-1450)
  ppm_co2 raw : 7.0 – 8.9  (dipakai: 7.4-8.0)
  ppm_acetone : 0.25– 1.21 (dipakai: 0.51-0.60) ← RENDAH untuk Bad
══════════════════════════════════════════════════════════════════
"""

import httpx
import time

BASE_URL  = "http://127.0.0.1:8000"
DEVICE_ID = 1   # ← Ganti dengan device_id milik perf_user_2199

CREDENTIALS = {
    "username": "perf_user_2199",
    "password": "SecurePassword123!"
}

# t-3 → t-2 → t-1 → t-0 (urutan kirim dari lama ke baru)
# Tren: nilai gas tinggi dan memburuk (polusi akut persisten)
# Pola khas Bad: puncak malam weekday, mq135 naik dari baseline tinggi
TIMESTEPS = [
    # t-3 (dikirim pertama)
    {"temperature": 30.2, "humidity": 81.5, "mq135": 460.0,
     "ppm_nh3": 1230.0, "ppm_co": 20.10, "ppm_co2": 7.4, "ppm_acetone": 0.51},
    # t-2
    {"temperature": 30.5, "humidity": 82.0, "mq135": 480.0,
     "ppm_nh3": 1310.0, "ppm_co": 21.80, "ppm_co2": 7.6, "ppm_acetone": 0.54},
    # t-1
    {"temperature": 30.8, "humidity": 82.5, "mq135": 500.0,
     "ppm_nh3": 1380.0, "ppm_co": 23.20, "ppm_co2": 7.8, "ppm_acetone": 0.57},
    # t-0 (dikirim terakhir — trigger inferensi model)
    {"temperature": 31.0, "humidity": 83.0, "mq135": 520.0,
     "ppm_nh3": 1450.0, "ppm_co": 24.50, "ppm_co2": 8.0, "ppm_acetone": 0.60},
]

LABEL_TARGET = "Bad"


def run():
    print(f"\n{'='*60}")
    print(f"  SEEDER — Target Label: {LABEL_TARGET}")
    print(f"  Polusi Akut, Kondisi Kritis Persisten")
    print(f"{'='*60}")

    with httpx.Client() as client:

        # 1. Login
        login_resp = client.post(f"{BASE_URL}/api/v1/token", data=CREDENTIALS)
        assert login_resp.status_code == 200, \
            f"Login gagal: {login_resp.status_code} — {login_resp.text}"
        token   = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"✅ Login berhasil")

        # 2. Kirim 4 timestep berurutan
        predicted_label = None
        for idx, payload in enumerate(TIMESTEPS):
            step  = f"t-{3 - idx}"
            is_t0 = (idx == len(TIMESTEPS) - 1)

            print(f"\n  → Kirim {step}"
                  f" | mq135={payload['mq135']:.1f}"
                  f" | ppm_co={payload['ppm_co']:.2f}"
                  f" | ppm_nh3={payload['ppm_nh3']:.1f}"
                  f" | ppm_acetone={payload['ppm_acetone']:.2f}")

            resp = client.post(
                f"{BASE_URL}/api/v1/sensors/log",
                json={"device_id": DEVICE_ID, **payload},
                headers=headers,
                timeout=30.0
            )

            if resp.status_code != 200:
                print(f"  ⚠️  HTTP {resp.status_code}: {resp.text}")
                return

            data = resp.json()
            print(f"  ← Response: {data}")

            if is_t0:
                predicted_label = data.get("realtime_classification", "N/A")

            if not is_t0:
                time.sleep(1.0)

        # 3. Evaluasi
        match = predicted_label == LABEL_TARGET
        print(f"\n{'='*60}")
        print(f"  TARGET    : {LABEL_TARGET}")
        print(f"  PREDIKSI  : {predicted_label}")
        print(f"  STATUS    : {'✅ BENAR — Pipeline sesuai' if match else '❌ SALAH — Cek pipeline'}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    run()