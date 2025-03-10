# Air Quality Monitoring System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This project is a comprehensive air quality monitoring system that gathers sensor data, predicts Air Quality Index (AQI), and provides historical data and future forecasts. The system consists of an ESP32-based sensor (not included in this repository), a Flask-based backend for data processing and model prediction, and a dynamic frontend for visualization.

## Features

*   **Real-time AQI Measurement:** Displays the current AQI based on sensor data.
*   **7-Day AQI Forecast:** Predicts the AQI for the next 7 days using an LSTM model.
*   **Sensor Data Visualization:** Showcases real-time sensor data (PM2.5, PM10, NOx, NH3, CO, Benzene).
*   **Weather Data Integration:** Fetches and displays current weather information (Temperature, Humidity, Pressure) from OpenWeatherMap API.
*   **Responsive Design:** A user-friendly interface that adapts to various screen sizes.

## Technologies Used

*   **Frontend:**
    *   HTML
    *   CSS
    *   JavaScript
*   **Backend:**
    *   Python
    *   Flask
    *   Flask-CORS
    *   Scikit-learn
    *   TensorFlow/Keras
    *   Joblib
    *   Pandas
    *   Gdown

## Setup Instructions

1.  **Clone the Repository:**

```bash
git clone [repository URL]
cd [repository name]

├── app.py             # Flask backend application
├── templates/
│   └── index.html     # Frontend HTML template
├── static/
│   ├── style.css      # Frontend CSS styles
│   ├── script.js      # Frontend JavaScript logic
│   ├── airco_logo.png   # Logo image (replace with your own)
│   └── new_york_city.jpg  # Location image (replace with your own)
├── aqi_model.pkl      # Trained Random Forest model
├── aqi_lstm_model.h5  # Trained LSTM model
├── aqi_test_data.csv  # Historical AQI data (for 7-day forecast)
└── README.md          # This file


Frontend Details
The frontend is built using HTML, CSS, and JavaScript. It dynamically fetches data from the Flask backend and OpenWeatherMap API. The main components are:

Header: Displays the application logo and title.

Location: Shows the location being monitored.

Current Air Quality: Visualizes the current AQI value with a progress bar and description.

Sensor Data: Displays real-time data from the connected sensors.

AQI Prediction (1 Hour): Displays the most recently recorded AQI (Since there is no backend function to generate the AQI) value.

7-Day AQI Forecast: Presents a 7-day AQI forecast with a detailed visual format.

Backend Details
The backend is built using Python and the Flask framework. It serves as the central processing unit for the system, handling sensor data, running machine learning models, and providing API endpoints for the frontend.

API Endpoints:

/sensor-data (POST): Receives sensor data from the ESP32 and returns the predicted AQI.

/predict-7day (GET): Predicts the AQI for the next 7 days using the LSTM model.

/get-latest-aqi (GET): Returns the latest AQI and sensor data.

Machine Learning Models:

Random Forest Model: Used for real-time AQI prediction based on sensor inputs.

LSTM Model: Used for predicting the AQI for the next 7 days.
Note: To generate 1-Hour AQI, the existing model must accept time as feature, or another model must be built for 1 hour prediction