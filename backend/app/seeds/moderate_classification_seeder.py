"""
══════════════════════════════════════════════════════════════════
SEEDER — Label: MODERATE
Uji pipeline TSC model xgb_model_A3 (Window=4)
══════════════════════════════════════════════════════════════════
Mengirim 4 data sensor berurutan (t-3 → t-0) untuk mensimulasikan
window klasifikasi Moderate.

Range Moderate:
  mq135       : 287 – 446  (dipakai: 300-360)
  ppm_co      : 2.1 – 10   (dipakai: 2.95-4.20)
  ppm_nh3     : 401 – 800  (dipakai: 420-520)
  ppm_co2 raw : 5.3 – 7.4  (dipakai: 5.8-6.4)
  ppm_acetone : 0.95– 2.81 (dipakai: 1.5-1.8) ← SEDANG untuk Moderate
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
# Tren: nilai gas naik bertahap (polusi merangkak persisten)
TIMESTEPS = [
    # t-3 (dikirim pertama)
    {"temperature": 26.2, "humidity": 70.5, "mq135": 300.0,
     "ppm_nh3": 420.0, "ppm_co": 2.95, "ppm_co2": 5.8, "ppm_acetone": 1.5},
    # t-2
    {"temperature": 26.5, "humidity": 71.0, "mq135": 320.0,
     "ppm_nh3": 460.0, "ppm_co": 3.40, "ppm_co2": 6.0, "ppm_acetone": 1.6},
    # t-1
    {"temperature": 26.8, "humidity": 71.5, "mq135": 340.0,
     "ppm_nh3": 490.0, "ppm_co": 3.80, "ppm_co2": 6.2, "ppm_acetone": 1.7},
    # t-0 (dikirim terakhir — trigger inferensi model)
    {"temperature": 27.0, "humidity": 72.0, "mq135": 360.0,
     "ppm_nh3": 520.0, "ppm_co": 4.20, "ppm_co2": 6.4, "ppm_acetone": 1.8},
]

LABEL_TARGET = "Moderate"


def run():
    print(f"\n{'='*60}")
    print(f"  SEEDER — Target Label: {LABEL_TARGET}")
    print(f"  Polusi Sedang, Tren Naik Persisten")
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