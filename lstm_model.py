import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ReduceLROnPlateau, EarlyStopping
from sklearn.preprocessing import MinMaxScaler
import pandas as pd

# Load dataset
df = pd.read_csv("city_day_cleaned.csv")
df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")
df.set_index("Date", inplace=True)
df = df.sort_index()

# Normalize data
scaler = MinMaxScaler(feature_range=(0, 1))
data_scaled = scaler.fit_transform(df)

# Define sequence length
look_back = 30  
forecast_days = 7  

# Function to create sequences
def create_sequences(data, look_back, forecast_days):
    X, y = [], []
    for i in range(len(data) - look_back - forecast_days + 1):
        X.append(data[i:(i + look_back), :-1])  
        y.append(data[i + look_back:i + look_back + forecast_days, -1])  
    return np.array(X), np.array(y)

# Prepare data
X, y = create_sequences(data_scaled, look_back, forecast_days)
split = int(len(X) * 0.8)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

# Reshape input for LSTM
X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], X_train.shape[2]))
X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], X_test.shape[2]))

# Define LSTM model
model = Sequential([
    LSTM(128, return_sequences=True, input_shape=(look_back, X_train.shape[2])),
    BatchNormalization(),
    Dropout(0.2),

    LSTM(64, return_sequences=True),
    BatchNormalization(),
    Dropout(0.2),

    LSTM(32),
    BatchNormalization(),
    Dropout(0.2),

    Dense(7)  
])

# Compile model
model.compile(optimizer=Adam(learning_rate=0.001), loss="mse")

# Callbacks
lr_scheduler = ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, verbose=1)
early_stopping = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)

# Train model
history = model.fit(
    X_train, y_train, 
    validation_data=(X_test, y_test), 
    epochs=50, 
    batch_size=64, 
    callbacks=[lr_scheduler, early_stopping],
    verbose=1
)

# Model summary
model.summary()
# Save the trained model
model.save("aqi_lstm_model.h5")
print("Model saved successfully!")

