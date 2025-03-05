import joblib
import pandas as pd
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Load trained AQI model
model = joblib.load("aqi_model.pkl")

# Expected feature names (must match training data)
FEATURE_NAMES = ["NH3", "NOx", "CO", "Benzene"]

latest_aqi = None  # Store latest AQI value

@app.route('/')
def index():
    return render_template('index.html', aqi=latest_aqi)

@app.route('/sensor-data', methods=['POST'])
def receive_data():
    global latest_aqi
    data = request.json

    # Convert JSON to a DataFrame with correct column names
    df = pd.DataFrame([[data["NH3"], data["NOx"], data["CO"], data["Benzene"]]], columns=FEATURE_NAMES)

    # Predict AQI
    latest_aqi = model.predict(df)[0]

    print(f"Received Data: {data}")
    print(f"Predicted AQI: {latest_aqi}")

    return jsonify({"aqi": latest_aqi})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
    