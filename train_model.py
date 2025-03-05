import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# Load dataset (replace with your actual file)
df = pd.read_csv("final_dataset.csv")  # Ensure this file contains NH3, NOx, CO, Benzene, and AQI

# Define features and target
FEATURES = ["NH3", "NOx", "CO", "Benzene"]
TARGET = "AQI"

X = df[FEATURES]
y = df[TARGET]

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize and train the RandomForestRegressor model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate model performance
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Model Performance: MAE = {mae:.2f}, R² = {r2:.2f}")

# Save the trained model
joblib.dump(model, "aqi_model.pkl")
print("Model saved as 'aqi_model.pkl'")
