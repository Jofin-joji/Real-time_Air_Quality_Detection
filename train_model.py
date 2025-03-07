import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib

# Load dataset (replace 'data.csv' with the actual filename)
df = pd.read_csv("data.csv")


# Drop rows with missing values
df.dropna(inplace=True)

# Define input features (X) and target variable (y)
X = df[["PM2.5", "PM10", "NOx", "Benzene", "NH3", "CO"]]
y = df["AQI"]

# Split data into training and testing sets (80% train, 20% test)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the Random Forest model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate model performance
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
print(f"Mean Absolute Error: {mae:.2f}")

# Save trained model
joblib.dump(model, "aqi_model.pkl")
print("Model saved as aqi_model.pkl")
