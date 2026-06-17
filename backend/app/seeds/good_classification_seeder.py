"""
══════════════════════════════════════════════════════════════════
SEEDER — Label: GOOD
Uji pipeline TSC model xgb_model_A3 (Window=4)
══════════════════════════════════════════════════════════════════
Mengirim 4 data sensor berurutan (t-3 → t-0) untuk mensimulasikan
window klasifikasi Good.

Range Good:
  mq135       : 117 – 312  (dipakai: 220-250)
  ppm_co      : 0   – 1.0  (dipakai: 0.80-0.86)
  ppm_nh3     : 0   – 200  (dipakai: 50-56)
  ppm_co2 raw : 2.3 – 5.7  (dipakai: 4.5-4.8)
  ppm_acetone : 2.46– 6.39 (dipakai: 3.5-3.8) ← TINGGI untuk Good
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
# Tren: nilai gas turun bertahap (udara membaik)
TIMESTEPS = [
    # t-3 (dikirim pertama)
    {"temperature": 23.6, "humidity": 59.5, "mq135": 250.0,
     "ppm_nh3": 56.0, "ppm_co": 0.86, "ppm_co2": 4.8, "ppm_acetone": 3.8},
    # t-2
    {"temperature": 23.4, "humidity": 59.0, "mq135": 240.0,
     "ppm_nh3": 54.0, "ppm_co": 0.84, "ppm_co2": 4.7, "ppm_acetone": 3.7},
    # t-1
    {"temperature": 23.2, "humidity": 58.5, "mq135": 230.0,
     "ppm_nh3": 52.0, "ppm_co": 0.82, "ppm_co2": 4.6, "ppm_acetone": 3.6},
    # t-0 (dikirim terakhir — trigger inferensi model)
    {"temperature": 23.0, "humidity": 58.0, "mq135": 220.0,
     "ppm_nh3": 50.0, "ppm_co": 0.80, "ppm_co2": 4.5, "ppm_acetone": 3.5},
]

LABEL_TARGET = "Good"


def run():
    print(f"\n{'='*60}")
    print(f"  SEEDER — Target Label: {LABEL_TARGET}")
    print(f"  Udara Bersih, Tren Membaik Stabil")
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
            step   = f"t-{3 - idx}"
            is_t0  = (idx == len(TIMESTEPS) - 1)

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