#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "JJ_JJ";  
const char* password = "Jofin123";  
const char* serverUrl = "http://192.168.31.92:5000/sensor-data";  

#define MQ135_PIN 34  
#define MQ7_PIN 35  
#define RL 10.0   // Load resistance in kΩ

// Store these values from calibration (update with actual values from Serial Monitor)
float R0_MQ135 = 54.67;  // Replace with your calibrated R0 for MQ135
float R0_MQ7 = 1.27;    // Replace with your calibrated R0 for MQ7

// Function to calculate sensor resistance (Rs)
float getSensorResistance(int pin) {
    int adc_value = analogRead(pin);
    float voltage = adc_value * (3.3 / 4095.0);  // Convert ADC to voltage
    float Rs = ((3.3 * RL) / voltage) - RL;  // Compute Rs using voltage divider formula
    return Rs   ;
}

// Convert Rs/R0 ratio to gas concentration using sensor curves
float calculatePPM(float Rs, float R0, float a, float b) {
    return a * pow((Rs / R0), b);  // Formula: PPM = a * (Rs/R0)^b
}

void setup() {
    Serial.begin(115200);
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi");

    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
    }

    Serial.println("\nConnected to WiFi");
}

void loop() {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;

        float Rs_MQ135 = getSensorResistance(MQ135_PIN);
        float Rs_MQ7 = getSensorResistance(MQ7_PIN);

        // Convert Rs to gas concentrations using sensor curves
        float ammonia = calculatePPM(Rs_MQ135, R0_MQ135, 44.947, -3.937);   // NH3 Curve
        float no2 = calculatePPM(Rs_MQ135, R0_MQ135, 102.2, -2.473);        // NO2 Curve
        float benzene = calculatePPM(Rs_MQ135, R0_MQ135, 3.027, -2.84);     // Benzene Curve
        float co = calculatePPM(Rs_MQ7, R0_MQ7, 1000.0, -1.5);              // CO Curve

        // Format JSON payload
        String jsonPayload = "{\"NH3\":" + String(ammonia) + 
                             ", \"NOx\":" + String(no2) + 
                             ", \"Benzene\":" + String(benzene) + 
                             ", \"CO\":" + String(co) + "}";

        // Send HTTP POST request to PC
        http.begin(serverUrl);
        http.addHeader("Content-Type", "application/json");

        int httpResponseCode = http.POST(jsonPayload);
        Serial.println("Data Sent: " + jsonPayload);
        Serial.println("Response Code: " + String(httpResponseCode));

        http.end();
    }

    delay(10000);  // Send data every 10 seconds
}
