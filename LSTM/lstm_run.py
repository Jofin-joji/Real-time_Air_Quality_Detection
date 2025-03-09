import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import MinMaxScaler
import os
import gdown

# ✅ Google Drive file ID (Extracted from your link)
file_id = "17rHFjcCUWt9x1iey5i5BLEaRCCfuvrKg"
file_path = "aqi_test_data.csv"

# ✅ Download dataset if not available
if not os.path.exists(file_path):
    print("📥 Downloading dataset from Google Drive...")
    gdown.download(f"https://drive.google.com/uc?id={file_id}", file_path, quiet=False)
    print("✅ Dataset downloaded successfully!")

# ✅ Load dataset
df = pd.read_csv(file_path)

# ✅ Fix date parsing issue
try:
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")  # Try expected format
except ValueError:
    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")  # Alternative format

# ✅ Define expected features
expected_features = ["PM2.5", "PM10", "NOx", "NH3", "CO", "Benzene"]

# ✅ Ensure all expected columns exist
missing_cols = [col for col in expected_features if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing columns in dataset: {missing_cols}")

# ✅ Separate features & keep "Date" column
df_features = df[expected_features]  # Keep only feature columns

# ✅ Normalize data
feature_scaler = MinMaxScaler()
df_scaled = feature_scaler.fit_transform(df_features)  

# ✅ Load trained model
try:
    model = keras.models.load_model("aqi_lstm_model.h5", custom_objects={"mse": keras.losses.MeanSquaredError()})
except TypeError:
    model = keras.models.load_model("aqi_lstm_model.h5", custom_objects={"mean_squared_error": keras.losses.MeanSquaredError()})

print("✅ Model loaded successfully!")

# ✅ Reshape input for LSTM
input_data = df_scaled[-1].reshape(1, 1, len(expected_features))

# ✅ Predict AQI for next 7 days
predicted_scaled = model.predict(input_data)  # Shape: (1, 7)

# 🚨 Fix: Use a separate scaler for AQI (not the feature scaler)
aqi_scaler = MinMaxScaler()
historical_aqi = df["PM2.5"].values.reshape(-1, 1)  # Assuming AQI is PM2.5
aqi_scaler.fit(historical_aqi)  # Fit only on AQI values

# ✅ Inverse transform predictions
predicted_aqi = aqi_scaler.inverse_transform(predicted_scaled.T).flatten()  # Transpose & flatten

# ✅ Generate the next 7 days' dates
last_date = df["Date"].max()  # Get the latest date in the dataset
future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 8)]

# ✅ Create a DataFrame for predictions
predictions_df = pd.DataFrame({"Date": future_dates, "Predicted_AQI": predicted_aqi})

# ✅ Print predictions
print("\n📊 Predicted AQI values for the next 7 days:\n", predictions_df)

# ✅ Save to CSV (Optional)
predictions_df.to_csv("predicted_aqi_next_7_days.csv", index=False)
print("\n✅ Predictions saved to 'predicted_aqi_next_7_days.csv'!")
