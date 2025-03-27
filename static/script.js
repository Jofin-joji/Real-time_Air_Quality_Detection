const apiKey = "83b133960256f36b41fab9d2508242c0"; // Replace with YOUR API KEY

let initialAqiValue; // Store the initial AQI value
let aqiUpdateTimeout; // Store the timeout ID

// Function to fetch current weather data (Temperature, Humidity, Pressure)
async function fetchWeatherData() {
    const city = "Kalady"; // Update the city name
    const latitude = 10.17; // Approximate latitude
    const longitude = 76.44; // Approximate longitude
    const apiUrl = `https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${apiKey}&units=metric`;

    try {
        const response = await fetch(apiUrl);
        const data = await response.json();

        if (response.ok) {
            // Check if data.main exists before accessing its properties
            if (data.main && data.main.temp !== undefined && data.main.humidity !== undefined && data.main.pressure !== undefined) {
                document.getElementById("temperature").textContent = data.main.temp + " °C";
                document.getElementById("humidity").textContent = data.main.humidity + " %";
                document.getElementById("pressure").textContent = data.main.pressure + " hPa";
            } else {
                console.error("Incomplete weather data received:", data);
                document.getElementById("temperature").textContent = "Error";
                document.getElementById("humidity").textContent = "Error";
            }
        } else {
            console.error("Error fetching weather data:", data.message);
            document.getElementById("temperature").textContent = "Error";
            document.getElementById("humidity").textContent = "Error";
            document.getElementById("pressure").textContent = "Error";
        }
    } catch (error) {
        console.error("Error fetching weather data:", error);
        document.getElementById("temperature").textContent = "Error";
        document.getElementById("humidity").textContent = "Error";
        document.getElementById("pressure").textContent = "Error";
    }
}


// Function to fetch sensor data and AQI from the Flask backend
async function fetchSensorData() {
    try {
        const response = await fetch("/get-latest-aqi"); // Replace with your actual endpoint
        const data = await response.json();

        document.getElementById("pm25").textContent = data["PM2.5"] !== undefined ? data["PM2.5"] + " μg/m³" : "-- μg/m³";
        document.getElementById("pm10").textContent = data["PM10"] !== undefined ? data["PM10"] + " μg/m³" : "-- μg/m³";
        document.getElementById("nh3").textContent = data["NH3"] !== undefined ? data["NH3"] + " ppm" : "-- ppm";
        document.getElementById("benzene").textContent = data["Benzene"] !== undefined ? data["Benzene"] + " ppm" : "-- ppm";
        document.getElementById("co").textContent = data["CO"] !== undefined ? data["CO"] + " ppm" : "-- ppm";
        document.getElementById("no2").textContent = data["NOx"] !== undefined ? data["NOx"] + " ppm" : "-- ppm";

        // Update AQI value and description
        const aqiValue = data["Predicted AQI"];

        document.getElementById("aqi-value").textContent = aqiValue !== undefined ? aqiValue.toFixed(0) : "--";
        const aqiDescription = getAQIDescription(aqiValue);
        document.getElementById("aqi-description").textContent = aqiDescription;

        // Update AQI progress bar
        updateAQIProgressBar(aqiValue);

        // Set 1-hour prediction to the current AQI value
        if (initialAqiValue === undefined) {
            initialAqiValue = aqiValue;  // Store the initial AQI value
            document.getElementById("aqi-prediction-value").textContent = aqiValue !== undefined ? aqiValue.toFixed(0) : "--";
            document.getElementById("aqi-prediction-confidence").textContent = "Average_AQI"; // Clear confidence message

            // Set a timeout to update the AQI after 1 hour
            aqiUpdateTimeout = setTimeout(() => {
                document.getElementById("aqi-prediction-value").textContent = aqiValue !== undefined ? aqiValue.toFixed(0) : "--";
                document.getElementById("aqi-prediction-confidence").textContent = "Updated after 1 Hour";
            }, 3600000); // 3600000 milliseconds = 1 hour

        }

        // Call Gemini API to get recommendations
        fetchGeminiResponse(aqiValue);

    } catch (error) {
        console.error("Error fetching sensor data:", error);
        document.getElementById("pm25").textContent = "Error";
        document.getElementById("pm10").textContent = "Error";
        document.getElementById("nh3").textContent = "Error";
        document.getElementById("benzene").textContent = "Error";
        document.getElementById("co").textContent = "Error";
        document.getElementById("no2").textContent = "Error";
        document.getElementById("aqi-value").textContent = "Error";
        document.getElementById("aqi-description").textContent = "Error";
        updateAQIProgressBar(0); // Reset progress bar
        document.getElementById("aqi-prediction-value").textContent = "Error";
        document.getElementById("aqi-prediction-confidence").textContent = "Error";
        clearTimeout(aqiUpdateTimeout);
    }
}

// Function to update AQI progress bar
function updateAQIProgressBar(aqi) {
    const progressBar = document.getElementById("aqi-progress");
    const percentage = Math.min(aqi / 300, 1) * 100; // Cap at 300+
    progressBar.style.width = percentage + "%";

    // Change color based on AQI category
    if (aqi <= 50) {
        progressBar.style.backgroundColor = "#2ecc71";
    } else if (aqi <= 100) {
        progressBar.style.backgroundColor = "#f1c40f";
    } else if (aqi <= 150) {
        progressBar.style.backgroundColor = "#e74c3c";
    } else if (aqi <= 200) {
        progressBar.style.backgroundColor = "#9b59b6";
    } else {
        progressBar.style.backgroundColor = "#34495e";
    }
}


// Function to get the description based on AQI value
function getAQIDescription(aqi) {
    if (aqi <= 50) {
        return "Good";
    } else if (aqi <= 100) {
        return "Moderate";
    } else if (aqi <= 150) {
        return "Poor";
    } else if (aqi <= 200) {
        return "Very Poor";
    } else {
        return "Hazardous";
    }
}

// Function to fetch 7-day AQI forecast from the Flask backend
async function fetch7DayForecast() {
    try {
        const response = await fetch("/predict-7day"); // Replace with your actual endpoint
        const forecastData = await response.json();

        const forecastContainer = document.getElementById("forecast-container");
        forecastContainer.innerHTML = ""; // Clear previous forecast

        forecastData.forEach(day => {
            const forecastDayDiv = document.createElement("div");
            forecastDayDiv.classList.add("forecast-day");

            // Determine AQI Category based on predicted value
            const aqiValue = day.Predicted_AQI;
            let aqiCategory = getAQIDescription(aqiValue);  // Get the category name

            // Add a class to the forecastDayDiv element based on the AQI category name
            forecastDayDiv.classList.add(aqiCategory);

            const date = new Date(day.Date);
            const dayName = date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });

            forecastDayDiv.innerHTML = `
                <div class="aqi-indicator"></div>
                <p class="date">${dayName}</p>
                <p class="aqi-value">${aqiValue.toFixed(0)}</p>
            `;
            forecastContainer.appendChild(forecastDayDiv);
        });

    } catch (error) {
        console.error("Error fetching 7-day forecast:", error);
    }
}
async function fetchAndVisualizeAqiTestData() {
    try {
        const response = await fetch("/aqi-test-data");
        const data = await response.json();

        if (data.error) {
            console.error("Error fetching aqi test data:", data.error);
            return;
        }

        const dates = data.dates;
        const pm25 = data.pm25;
        const pm10 = data.pm10;
        const nox = data.nox;
        const nh3 = data.nh3;
        const co = data.co;
        const benzene = data.benzene;

        // Create the chart using Chart.js
        const ctx = document.getElementById('pollutantChart').getContext('2d');
        const myChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'PM2.5',
                        data: pm25,
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1,
                        fill: false
                    },
                    {
                        label: 'PM10',
                        data: pm10,
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1,
                        fill: false
                    },
                    {
                        label: 'NOx',
                        data: nox,
                        borderColor: 'rgba(255, 206, 86, 1)',
                        borderWidth: 1,
                        fill: false
                    },
                    {
                        label: 'NH3',
                        data: nh3,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1,
                        fill: false
                    },
                    {
                        label: 'CO',
                        data: co,
                        borderColor: 'rgba(153, 102, 255, 1)',
                        borderWidth: 1,
                        fill: false
                    },
                    {
                        label: 'Benzene',
                        data: benzene,
                        borderColor: 'rgba(255, 159, 64, 1)',
                        borderWidth: 1,
                        fill: false
                    }
                ]
            },
            options: {
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Pollutant Level'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'aqi_test_data.csv Pollutant Levels'
                    }
                }
            }
        });

    } catch (error) {
        console.error("Error fetching or visualizing pollutant data:", error);
    }
}
// New function to fetch Gemini response
async function fetchGeminiResponse(aqiValue) {
    try {
        const response = await fetch("/get-gemini-response", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ aqi: aqiValue }),
        });

        const data = await response.json();

        if (data.error) {
            console.error("Error fetching Gemini response:", data.error);
            document.getElementById("gemini-response").textContent = "Error fetching recommendations.";
        } else {
            // Format the Gemini response as a bulleted list
            const recommendations = data.response.split('\n'); // Split response into lines
            let formattedResponse = "<ul>";
            recommendations.forEach(recommendation => {
                if (recommendation.trim() !== "") {  // Ignore empty lines
                    formattedResponse += `<li>${recommendation.trim()}</li>`; // Add each line as a list item
                }
            });
            formattedResponse += "</ul>";
            document.getElementById("gemini-response").innerHTML = formattedResponse; // Display the formatted response
        }
    } catch (error) {
        console.error("Error calling Gemini API:", error);
        document.getElementById("gemini-response").textContent = "Error calling recommendation service.";
    }
}

// Call the functions to fetch data when the page loads
window.onload = () => {
    fetchWeatherData();
    fetchSensorData();
    fetch7DayForecast();
    fetchAndVisualizeAqiTestData(); // Call the new function

    // Refresh sensor data every 10 seconds (adjust as needed)
    setInterval(fetchSensorData, 10000);
    setInterval(fetchWeatherData, 60000); // Refresh weather data every minute
};