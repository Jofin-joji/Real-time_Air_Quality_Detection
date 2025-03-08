#include <WiFi.h>
#include <HTTPClient.h>
#include <HardwareSerial.h>

const char* ssid = "JJ_JJ";
const char* password = "Jofin123";
const char* serverUrl = "http://192.168.31.91:5000/sensor-data";

#define MQ135_PIN 34
#define MQ7_PIN 35
#define RL 10.0   // Load resistance in kΩ
#define PMS_RX 16  // Connect to PMS7003 TX
#define PMS_TX -1  // Not needed

// Store these values from calibration (update with actual values from Serial Monitor)
float R0_MQ135 = 54.67;  // Replace with your calibrated R0 for MQ135
float R0_MQ7 = 1.27;    // Replace with your calibrated R0 for MQ7

HardwareSerial pmsSerial(1);  // PMS7003 uses UART1

// Function to calculate sensor resistance (Rs)
float getSensorResistance(int pin) {
    int adc_value = analogRead(pin);
    float voltage = adc_value * (3.3 / 4095.0);
    float Rs = ((3.3 * RL) / voltage) - RL;
    return Rs;
}

// Convert Rs/R0 ratio to gas concentration using sensor curves
float calculatePPM(float Rs, float R0, float a, float b) {
    return a * pow((Rs / R0), b);
}

// Function to wake up PMS7003 (prevents it from sleeping)
void wakeUpPMS7003() {
    Serial.println("🌟 Waking up PMS7003...");
    uint8_t wakeCommand[] = {0x42, 0x4D, 0xE4, 0x00, 0x01, 0x73};
    pmsSerial.write(wakeCommand, sizeof(wakeCommand));
    delay(1000);  // Give it time to wake up
}

// Function to flush Serial buffer (fixes buffer overflow issues)
void flushSerial() {
    while (pmsSerial.available()) {
        pmsSerial.read();  // Clear buffer
    }
}

// Function to read PM2.5 and PM10 values from PMS7003
bool readPMS7003(uint16_t &pm25, uint16_t &pm10) {
    flushSerial();  // Clear old buffer data
    wakeUpPMS7003(); // Ensure the sensor is active

    if (pmsSerial.available() >= 32) {
        uint8_t buffer[32];
        pmsSerial.readBytes(buffer, 32);

        if (buffer[0] == 0x42 && buffer[1] == 0x4D) {  // Check packet header
            pm25 = (buffer[12] << 8) | buffer[13];
            pm10 = (buffer[14] << 8) | buffer[15];
            return true;
        }
    }

    Serial.println("❌ Failed to read PMS7003 data");
    return false;
}

void setup() {
    Serial.begin(115200);
    pmsSerial.begin(9600, SERIAL_8N1, PMS_RX, PMS_TX);
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi");

    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
    }
    Serial.println("\n✅ Connected to WiFi");
}

void loop() {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        float Rs_MQ135 = getSensorResistance(MQ135_PIN);
        float Rs_MQ7 = getSensorResistance(MQ7_PIN);
        
        // Convert Rs to gas concentrations using sensor curves
        float ammonia = calculatePPM(Rs_MQ135, R0_MQ135, 44.947, -3.937);
        float no2 = calculatePPM(Rs_MQ135, R0_MQ135, 102.2, -2.473);
        float benzene = calculatePPM(Rs_MQ135, R0_MQ135, 3.027, -2.84);
        float co = calculatePPM(Rs_MQ7, R0_MQ7, 1000.0, -1.5);

        uint16_t pm25 = 0, pm10 = 0;
        if (!readPMS7003(pm25, pm10)) {
            Serial.println("❌ Failed to read PMS7003 data");
        }

        // Format JSON payload
        String jsonPayload = "{";
        jsonPayload += "\"NH3\": " + String(ammonia) + ", ";
        jsonPayload += "\"NOx\": " + String(no2) + ", ";
        jsonPayload += "\"Benzene\": " + String(benzene) + ", ";
        jsonPayload += "\"CO\": " + String(co) + ", ";
        jsonPayload += "\"PM2.5\": " + String(pm25) + ", ";
        jsonPayload += "\"PM10\": " + String(pm10) + "}";

        // Send HTTP POST request to PC
        http.begin(serverUrl);
        http.addHeader("Content-Type", "application/json");

        int httpResponseCode = http.POST(jsonPayload);
        Serial.println("📤 Data Sent: " + jsonPayload);
        Serial.println("🔹 Response Code: " + String(httpResponseCode));

        http.end();
    }

    // Restart sensor every 5 minutes to avoid long-term failures
    if (millis() % 300000 < 10000) {  
        wakeUpPMS7003();
    }

    delay(10000);  // Send data every 10 seconds
}
