import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

# ---------------------------------------
# LOAD DATASET
# ---------------------------------------
df = pd.read_csv("sensor_dataset_5000.csv")

# Features
X = df[["BPM", "SpO2", "Temperature_C", "Humidity_%", 
        "GSR", "Angle_X", "Angle_Y"]]

# OUTPUT-1: Heat Therapy
y1 = df["Heat_Therapy_Duration"]

# OUTPUT-2: Sleep Quality
y2 = df["Sleep_Quality"]

# Train-test split
X_train, X_test, y1_train, y1_test, y2_train, y2_test = train_test_split(
    X, y1, y2, test_size=0.25, random_state=42
)

# ---------------------------------------
# SCALING (SHARED SCALER)
# ---------------------------------------
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

joblib.dump(scaler, "scaler.pkl")
print("Scaler saved: scaler.pkl")

# ---------------------------------------
# MODEL 1: HEAT THERAPY MODEL
# ---------------------------------------
heat_model = KNeighborsRegressor(n_neighbors=5)
heat_model.fit(X_train_scaled, y1_train)

joblib.dump(heat_model, "heat_model.pkl")
print("Heat Therapy Model saved: heat_model.pkl")

# ---------------------------------------
# MODEL 2: SLEEP QUALITY MODEL
# ---------------------------------------
sleep_model = KNeighborsRegressor(n_neighbors=5)
sleep_model.fit(X_train_scaled, y2_train)

joblib.dump(sleep_model, "sleep_model.pkl")
print("Sleep Quality Model saved: sleep_model.pkl")

# ---------------------------------------
# PERFORMANCE METRICS
# ---------------------------------------
y1_pred = heat_model.predict(X_test_scaled)
y2_pred = sleep_model.predict(X_test_scaled)

def metrics(true, pred, name):
    print(f"\n===== {name} =====")
    print("MAE :", mean_absolute_error(true, pred))
    print("RMSE:", np.sqrt(mean_squared_error(true, pred)))
    print("R²  :", r2_score(true, pred))

metrics(y1_test, y1_pred, "Heat Therapy Duration Model")
metrics(y2_test, y2_pred, "Sleep Quality Model")
