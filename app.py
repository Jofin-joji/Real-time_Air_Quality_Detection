from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import MinMaxScaler
import os

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Requests

# ✅ Load trained Random Forest model
rf_model = joblib.load("aqi_model.pkl")

# ✅ Load trained LSTM model with fixes
try:
    lstm_model = keras.models.load_model("aqi_lstm_model.h5", custom_objects={"mse": keras.losses.MeanSquaredError()}, safe_mode=False)
except Exception as e:
    print(f"⚠️ Error loading LSTM model: {e}")
    lstm_model = None  # Set to None to prevent crashes

# ✅ Store latest prediction
latest_data = {}

@app.route("/sensor-data", methods=["POST"])
def predict_aqi():
    """
    Predict real-time AQI using the Random Forest model.
    """
    global latest_data

    try:
        data = request.json  # Get JSON from ESP32

        # Extract sensor values
        pm25 = data.get("PM2.5", 0)
        pm10 = data.get("PM10", 0)
        nox = data.get("NOx", 0)
        benzene = data.get("Benzene", 0)
        nh3 = data.get("NH3", 0)
        co = data.get("CO", 0)

        # Prepare input for model
        input_features = np.array([[pm25, pm10, nox, benzene, nh3, co]])

        # Predict AQI
        predicted_aqi = rf_model.predict(input_features)[0]

        latest_data = {
            "PM2.5": pm25,
            "PM10": pm10,
            "NOx": nox,
            "Benzene": benzene,
            "NH3": nh3,
            "CO": co,
            "Predicted AQI": round(predicted_aqi, 2),
        }

        print(f"Received Data: {data}")
        print(f"Predicted AQI: {round(predicted_aqi, 2)}")

        return jsonify(latest_data)

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/predict-7day", methods=["GET"])
def predict_7day_aqi():
    """
    Predict the next 7 days of AQI using the LSTM model.
    """
    try:
        if lstm_model is None:
            return jsonify({"error": "LSTM model failed to load. Check server logs."})

        # ✅ Google Drive file ID
        file_id = "17rHFjcCUWt9x1iey5i5BLEaRCCfuvrKg"
        file_path = "aqi_test_data.csv"

        # ✅ Download dataset if not available
        if not os.path.exists(file_path):
            import gdown
            print("📥 Downloading dataset from Google Drive...")
            gdown.download(f"https://drive.google.com/uc?id={file_id}", file_path, quiet=False)
            print("✅ Dataset downloaded successfully!")

        # ✅ Load dataset
        df = pd.read_csv(file_path)

        # ✅ Parse date
        try:
            df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")
        except ValueError:
            df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")

        # ✅ Extract features
        expected_features = ["PM2.5", "PM10", "NOx", "NH3", "CO", "Benzene"]
        df_features = df[expected_features]

        # ✅ Normalize data
        feature_scaler = MinMaxScaler()
        df_scaled = feature_scaler.fit_transform(df_features)

        # ✅ Reshape input for LSTM
        input_data = df_scaled[-1].reshape(1, 1, len(expected_features))

        # ✅ Predict AQI for next 7 days
        predicted_scaled = lstm_model.predict(input_data)  # Shape: (1, 7)

        # ✅ Inverse transform predictions
        aqi_scaler = MinMaxScaler()
        historical_aqi = df["PM2.5"].values.reshape(-1, 1)
        aqi_scaler.fit(historical_aqi)

        predicted_aqi = aqi_scaler.inverse_transform(predicted_scaled.T).flatten()

        # ✅ Generate the next 7 days' dates
        last_date = df["Date"].max()
        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 8)]

        # ✅ Create a DataFrame for predictions
        predictions_df = pd.DataFrame({"Date": future_dates, "Predicted_AQI": predicted_aqi})

        return jsonify(predictions_df.to_dict(orient="records"))

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/get-latest-aqi", methods=["GET"])
def get_latest_aqi():
    return jsonify(latest_data)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
