# ============================================================
# Heat Therapy + Sleep Quality Predictor (KNN + IP Fetch Loop)
# ========== FULL MODIFIED CODE (HTML PARSING + JOBLIB) ======
# ============================================================

import requests
import joblib
import numpy as np
import time
import re

# ------------------------------------------------------------
# Load trained models and scaler (JOBLIB)
# ------------------------------------------------------------
heat_model = joblib.load("heat_model.pkl")
sleep_model = joblib.load("sleep_model.pkl")
scaler = joblib.load("scaler.pkl")

# ------------------------------------------------------------
# IP of your NodeMCU / ESP / STM32 Web Server
# ------------------------------------------------------------
BASE_IP = "http://192.168.137.61"   # <--- CHANGE THIS

# ------------------------------------------------------------
# ThingSpeak
# ------------------------------------------------------------
TS_API_KEY = "3J6LJDI7PCAU2IVL"
TS_URL = "https://api.thingspeak.com/update"

print("🔥 Heat & Sleep Prediction System Started!")
print("-------------------------------------------")

first_call = True   # first request → sleep = 0

# ------------------------------------------------------------
# Helper for regex extraction from HTML
# ------------------------------------------------------------
def extract(pattern, text, default=0.0):
    match = re.search(pattern, text)
    if match:
        try:
            return float(match.group(1))
        except:
            return default
    return default


# ------------------------------------------------------------
# MAIN LOOP
# ------------------------------------------------------------
while True:
    try:
        # ----------------------------------------------------
        # FETCH SENSOR DATA FROM DEVICE
        # ----------------------------------------------------
        url = f"{BASE_IP}/"
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            time.sleep(3)
            continue

        data = response.text.strip()
        print("\n📡 Received HTML from device:\n", data)

        # ----------------------------------------------------
        # PARSE SENSOR VALUES FROM HTML <p><b> TAGS
        # ----------------------------------------------------
        bpm       = extract(r"BPM:</b>\s*([\d\.\-]+)", data)
        spo2      = extract(r"SpO2:</b>\s*([\d\.\-]+)", data)
        temp      = extract(r"Temperature:</b>\s*([\d\.\-]+)", data)
        humidity  = extract(r"Humidity:</b>\s*([\d\.\-]+)", data)
        gsr       = extract(r"GSR:</b>\s*([\d\.\-]+)", data)

        xy_match = re.search(r"X:</b>\s*([\d\.\-]+).*?Y:</b>\s*([\d\.\-]+)", data)
        if xy_match:
            x = float(xy_match.group(1))
            y = float(xy_match.group(2))
        else:
            x = 0.0
            y = 0.0

        print(f"Parsed → BPM:{bpm}, SpO2:{spo2}, Temp:{temp}, Hum:{humidity}, "
              f"GSR:{gsr}, X:{x}, Y:{y}")

        # ----------------------------------------------------
        # PREPARE INPUT FOR MODEL
        # ----------------------------------------------------
        features = np.array([[bpm, spo2, temp, humidity, gsr, x, y]])
        features_scaled = scaler.transform(features)

        # ----------------------------------------------------
        # PREDICT
        # ----------------------------------------------------
        heat_value = float(heat_model.predict(features_scaled)[0])

        if first_call:
            sleep_value = 0
            first_call = False
        else:
            sleep_value = float(sleep_model.predict(features_scaled)[0])

        print(f"🔥 Heat Prediction = {heat_value}")
        print(f"😴 Sleep Prediction = {sleep_value}")

        # ----------------------------------------------------
        # SEND BACK HEAT VALUE TO DEVICE
        # ----------------------------------------------------
        send_url = f"{BASE_IP}/{heat_value}"

        try:
            send_resp = requests.get(send_url, timeout=5)
            if send_resp.status_code == 200:
                print(f"📤 Sent heat value → /{heat_value}")
            else:
                print(f"❌ Device rejected heat value (HTTP {send_resp.status_code})")
        except:
            print("⚠️ Cannot reach device for prediction callback")

        # ----------------------------------------------------
        # SEND TO THINGSPEAK
        # ----------------------------------------------------
        payload = {
            "api_key": TS_API_KEY,
            "field1": bpm,
            "field2": spo2,
            "field3": temp,
            "field4": humidity,
            "field5": gsr,
            "field6": heat_value,
            "field7": sleep_value
        }

        try:
            ts_resp = requests.get(TS_URL, params=payload, timeout=5)
            print("📡 ThingSpeak Response:", ts_resp.text)
        except:
            print("❌ ThingSpeak Error")

        print("-------------------------------------------")
        time.sleep(3)

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
        break

    except Exception as e:
        print("❌ Unexpected Error:", e)
        time.sleep(3)
