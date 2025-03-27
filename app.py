from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import MinMaxScaler
import os
import smtplib
from email.mime.text import MIMEText
import ssl  # Import the ssl module
import time  # Import the time module

import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend when no display is available
import matplotlib.pyplot as plt

import google.generativeai as genai  # Import the Gemini API library

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Requests

# Load trained Random Forest model
try:
    rf_model = joblib.load("aqi_model.pkl")
    print("✅ Random Forest model loaded successfully!")
except Exception as e:
    rf_model = None
    print(f"❌ Error loading Random Forest model: {e}")

# Load trained LSTM model with fixes
try:
    lstm_model = keras.models.load_model("aqi_lstm_model.h5", custom_objects={"mse": keras.losses.MeanSquaredError()}, safe_mode=False)
    print("✅ LSTM model loaded successfully!")
except Exception as e:
    lstm_model = None
    print(f"❌ Error loading LSTM model: {e}")

# Store latest prediction
latest_data = {}

# Email configuration
SENDER_EMAIL = "kid001creative@gmail.com"  # Replace with your email
SENDER_PASSWORD = "imoe yets ptjj grdo"  # Replace with your password or App Password if using Gmail
RECEIVER_EMAIL = "kid0002creative@gmail.com"  # Replace with recipient email

# Rate limiting variables
last_email_time = 0  # Initialize last email time
EMAIL_INTERVAL = 30 * 60  # 30 minutes in seconds

# Initialize Gemini API
try:
    GOOGLE_API_KEY = "AIzaSyBBRfLUx8CRebFItO20Uuvhz0zA6mMeYpE"  # Replace with your actual Gemini API key HERE! - VERY RISKY
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')  # Or 'gemini-1.5-pro-latest'
    print("✅ Gemini API initialized successfully!")
except Exception as e:
    model = None
    print(f"❌ Error initializing Gemini API: {e}")


def send_email(aqi_value):
    """Sends an email notification when AQI exceeds 125."""
    subject = "Air Quality Alert: AQI Exceeds Threshold!"
    body = f"The Air Quality Index (AQI) has reached {aqi_value}, exceeding the threshold of 125. Please take necessary precautions."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    try:
        # Create a secure SSL context
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            print("📧 Email notification sent successfully!")
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication Error: {e}")
        print("Please check your email and password. If using Gmail, ensure 'Less secure app access' is enabled or use an App Password.")
    except Exception as e:
        print(f"❌ Error sending email: {e}")


@app.route("/sensor-data", methods=["POST"])
def predict_aqi():
    """
    Predict real-time AQI using the Random Forest model.
    """
    global latest_data, last_email_time  # Access global variables

    if rf_model is None:
        return jsonify({"error": "Random Forest model is not loaded."}), 500

    try:
        data = request.get_json()  # Get JSON from ESP32

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
        try:
            predicted_aqi = rf_model.predict(input_features)[0]
        except Exception as e:
            print(f"❌ Error during prediction: {e}")
            return jsonify({"error": f"Prediction failed: {e}"}), 500

        predicted_aqi_rounded = round(predicted_aqi, 2)

        latest_data = {
            "PM2.5": pm25,
            "PM10": pm10,
            "NOx": nox,
            "Benzene": benzene,
            "NH3": nh3,
            "CO": co,
            "Predicted AQI": predicted_aqi_rounded,
        }

        print(f"✅ Received Data: {data}")
        print(f"✅ Predicted AQI: {predicted_aqi_rounded}")

        # Send email if AQI is above threshold and rate limit is not exceeded
        current_time = time.time()
        if predicted_aqi > 100 and (current_time - last_email_time >= EMAIL_INTERVAL):
            send_email(predicted_aqi_rounded)
            last_email_time = current_time  # Update last email time

        return jsonify(latest_data)

    except Exception as e:
        print(f"❌ Error processing sensor data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/predict-7day", methods=["GET"])
def predict_7day_aqi():
    """
    Predict the next 7 days of AQI using the LSTM model.
    """
    if lstm_model is None:
        return jsonify({"error": "LSTM model is not loaded."}), 500

    try:
        # ✅ Google Drive file ID
        file_id = "17rHFjcCUWt9x1iey5i5BLEaRCCfuvrKg"
        file_path = "aqi_test_data.csv"

        # ✅ Download dataset if not available
        if not os.path.exists(file_path):
            import gdown
            print("📥 Downloading dataset from Google Drive...")
            try:
                gdown.download(f"https://drive.google.com/uc?id={file_id}", file_path, quiet=False)
                print("✅ Dataset downloaded successfully!")
            except Exception as e:
                print(f"❌ Error downloading dataset: {e}")
                return jsonify({"error": f"Failed to download dataset: {e}"}), 500

        # ✅ Load dataset
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"❌ Error reading CSV file: {e}")
            return jsonify({"error": f"Failed to read CSV: {e}"}), 500

        # ✅ Parse date
        try:
            df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
        except ValueError:
            try:
                df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")
            except Exception as e:
                print(f"❌ Error parsing dates: {e}")
                return jsonify({"error": f"Failed to parse dates: {e}"}), 500

        # ✅ Extract features
        expected_features = ["PM2.5", "PM10", "NOx", "NH3", "CO", "Benzene"]
        df_features = df[expected_features]

        # ✅ Normalize data
        feature_scaler = MinMaxScaler()
        df_scaled = feature_scaler.fit_transform(df_features)

        # ✅ Reshape input for LSTM
        input_data = df_scaled[-1].reshape(1, 1, len(expected_features))

        # ✅ Predict AQI for next 7 days
        try:
            predicted_scaled = lstm_model.predict(input_data)  # Shape: (1, 7)
        except Exception as e:
            print(f"❌ LSTM Prediction Error: {e}")
            return jsonify({"error": f"LSTM Prediction failed: {e}"}), 500

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
        print(f"❌ General Error predicting 7-day AQI: {e}")
        return jsonify({"error": str(e)}), 500

def load_aqi_test_data():
    """Loads the aqi_test_data.csv."""
    file_id = "17rHFjcCUWt9x1iey5i5BLEaRCCfuvrKg"  # Replace with the actual file ID, though it seems you already have this correct
    file_path = "aqi_test_data.csv"

    # Download dataset if not available
    if not os.path.exists(file_path):
        import gdown
        print("📥 Downloading aqi_test_data.csv from Google Drive...")
        try:
            gdown.download(f"https://drive.google.com/uc?id={file_id}", file_path, quiet=False)
            print("✅ aqi_test_data.csv downloaded successfully!")
        except Exception as e:
            print(f"❌ Error downloading aqi_test_data.csv: {e}")
            return None  # Indicate failure

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"❌ Error reading aqi_test_data.csv: {e}")
        return None

    try:
        df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
    except ValueError:
        try:
            df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")
        except Exception as e:
            print(f"❌ Error parsing dates in aqi_test_data.csv: {e}")
            return None

    return df

@app.route("/aqi-test-data")
def get_aqi_test_data():
    """Returns the aqi_test_data for visualization."""
    try:
        df = load_aqi_test_data() # Load dataset now
        if df is None:
            return jsonify({"error": "Failed to load aqi_test_data.csv"}), 500

        pollutant_data = {
            "dates": df["Date"].dt.strftime("%Y-%m-%d").tolist(),  # Format dates for JSON
            "pm25": df["PM2.5"].tolist(),
            "pm10": df["PM10"].tolist(),
            "nox": df["NOx"].tolist(),
            "nh3": df["NH3"].tolist(),
            "co": df["CO"].tolist(),
            "benzene": df["Benzene"].tolist(),
        }
        return jsonify(pollutant_data)
    except Exception as e:
        print(f"❌ Error in get_aqi_test_data endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/get-latest-aqi", methods=["GET"])
def get_latest_aqi():
    return jsonify(latest_data)

@app.route("/get-gemini-response", methods=["POST"])
def get_gemini_response():
    """
    Gets a response from the Gemini API based on the current AQI.
    """
    if model is None:
        return jsonify({"error": "Gemini API is not initialized."}), 500

    try:
        data = request.get_json()
        aqi_value = data.get("aqi", None)
        if aqi_value is None:
            return jsonify({"error": "AQI value is missing in the request."}), 400

        # Construct the prompt with more context
        prompt = f"""The current Air Quality Index (AQI) is {aqi_value}. This reading was obtained in real time from my personal air quality monitoring system. 
        Provide detailed and concise recommendations to protect the health of local residents. Format each recommendation as a bullet point (* Recommendation).

        Specifically include:

        * Specific actions to take based on the AQI level
        * Vulnerable populations who are most at risk
        * Ways to reduce personal contribution to pollution
        * precations to be taken under the heading precations
        * list representions should be used

        Keep the recommendations clear, actionable, and under 100 words.
        """

        try:
            response = model.generate_content(prompt)
            gemini_response = response.text
            print(f"✅ Gemini API Response: {gemini_response}")
            return jsonify({"response": gemini_response})
        except Exception as e:
            print(f"❌ Error generating content with Gemini API: {e}")
            return jsonify({"error": f"Gemini API error: {e}"}), 500

    except Exception as e:
        print(f"❌ Error processing Gemini API request: {e}")
        return jsonify({"error": str(e)}), 500



@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)