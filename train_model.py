import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
from scipy.stats import randint

# --- Configuration ---
DATA_FILE = "data.csv"
MODEL_SAVE_PATH = "aqi_model.pkl"
TEST_SIZE = 0.2
RANDOM_STATE = 42 # Ensures reproducibility

# --- 1. Load and Prepare Data ---
print(f"Loading data from {DATA_FILE}...")
try:
    df = pd.read_csv(DATA_FILE)
except FileNotFoundError:
    print(f"Error: File not found at {DATA_FILE}")
    exit()

print("Initial dataset shape:", df.shape)

# Handle missing values (using dropna as in the original, but be mindful if data loss is significant)
initial_rows = len(df)
df.dropna(inplace=True)
final_rows = len(df)
print(f"Dropped {initial_rows - final_rows} rows with missing values.")
print("Dataset shape after dropping NaNs:", df.shape)

if df.empty:
    print("Error: Dataset is empty after dropping missing values. Cannot proceed.")
    exit()

# Define features (X) and target (y)
# Ensure column names exactly match your CSV header
features = ["PM2.5", "PM10", "NOx", "Benzene", "NH3", "CO"]
target = "AQI"

try:
    X = df[features]
    y = df[target]
except KeyError as e:
    print(f"Error: Column not found in CSV: {e}. Please check column names.")
    print(f"Available columns: {df.columns.tolist()}")
    exit()

# --- 2. Split Data ---
print(f"Splitting data ({int((1-TEST_SIZE)*100)}% train, {int(TEST_SIZE*100)}% test)...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)
print(f"Training set size: {X_train.shape[0]} samples")
print(f"Testing set size: {X_test.shape[0]} samples")

# --- 3. Hyperparameter Tuning with RandomizedSearchCV ---
print("Starting hyperparameter tuning with RandomizedSearchCV...")

# Define the parameter distribution for Randomized Search
# These ranges cover common effective values for Random Forests
param_dist = {
    'n_estimators': randint(100, 1000), # Number of trees
    'max_depth': [10, 20, 30, 40, 50, None], # Max depth of trees (None means unlimited)
    'min_samples_split': randint(2, 20), # Min samples to split a node
    'min_samples_leaf': randint(1, 10), # Min samples in a leaf node
    'max_features': ['sqrt', 'log2', 0.6, 0.8, 1.0], # Number of features to consider for best split
    'bootstrap': [True, False] # Whether to use bootstrap samples
}

# Base model
rf = RandomForestRegressor(random_state=RANDOM_STATE)

# Randomized Search setup
# n_iter controls how many parameter settings are tried. Increase for more thorough search.
# cv=5 means 5-fold cross-validation.
# scoring='neg_mean_absolute_error' because RandomizedSearchCV maximizes score, and we want to minimize MAE.
# n_jobs=-1 uses all available CPU cores for faster search.
random_search = RandomizedSearchCV(estimator=rf,
                                   param_distributions=param_dist,
                                   n_iter=100, # Number of parameter settings to sample
                                   cv=5,
                                   verbose=1, # Set to 1 or 2 for more details during search
                                   random_state=RANDOM_STATE,
                                   n_jobs=-1,
                                   scoring='neg_mean_absolute_error') # Lower MAE is better

# Fit Randomized Search to the training data
random_search.fit(X_train, y_train)

print("\nHyperparameter tuning finished.")
print("Best parameters found:")
print(random_search.best_params_)

# Get the best model found by the search
best_model = random_search.best_estimator_

# --- 4. Evaluate the Best Model ---
print("\nEvaluating the best model on the test set...")
y_pred = best_model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)

print(f"Mean Absolute Error (MAE): {mae:.2f}")
print(f"Mean Squared Error (MSE): {mse:.2f}")
print(f"Root Mean Squared Error (RMSE): {rmse:.2f}")
print(f"R-squared (R²): {r2:.4f}")

# --- 5. Save the Optimized Model ---
joblib.dump(best_model, MODEL_SAVE_PATH)
print(f"\nOptimized model saved as {MODEL_SAVE_PATH}")

# --- Optional: Feature Importance ---
print("\nFeature Importances from the best model:")
importances = best_model.feature_importances_
feature_importance_df = pd.DataFrame({'feature': features, 'importance': importances})
feature_importance_df = feature_importance_df.sort_values('importance', ascending=False)
print(feature_importance_df)