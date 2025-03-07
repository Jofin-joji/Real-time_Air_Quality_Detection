from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import joblib
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Requests

# Load trained model
model = joblib.load("aqi_model.pkl")

# Store latest prediction
latest_data = {}

@app.route("/sensor-data", methods=["POST"])
def predict_aqi():
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

        # Prepare input for model (excluding Date)
        input_features = np.array([[pm25, pm10, nox, benzene, nh3, co]])

        # Predict AQI
        predicted_aqi = model.predict(input_features)[0]

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

# API to fetch latest AQI data for webpage
@app.route("/get-latest-aqi", methods=["GET"])
def get_latest_aqi():
    return jsonify(latest_data)

# Serve the webpage
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
