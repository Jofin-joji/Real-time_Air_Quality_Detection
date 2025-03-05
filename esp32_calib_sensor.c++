#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "JJ_JJ";  
const char* password = "Jofin123";  
#define MQ135_PIN 34  
#define MQ7_PIN 35  
#define RL 10.0   // Load resistance in kΩ

float R0_MQ135 = 0;
float R0_MQ7 = 0;

// Function to calculate sensor resistance (Rs)
float getSensorResistance(int pin) {
    int adc_value = analogRead(pin);
    float voltage = adc_value * (3.3 / 4095.0);  // Convert ADC to voltage (ESP32 ADC is 12-bit)
    float Rs = ((3.3 * RL) / voltage) - RL;  // Compute Rs
    return Rs;
}

// Calibrate MQ135 using CO2 concentration in clean air (~400 ppm)
void calibrateMQ135() {
    float Rs_air = getSensorResistance(MQ135_PIN);
    R0_MQ135 = Rs_air / 3.6;  // 3.6 is the Rs/R0 ratio for CO2 at 400 ppm
    Serial.print("MQ135 R0: ");
    Serial.println(R0_MQ135);
}

// Calibrate MQ7 using CO concentration in clean air (~1 ppm)
void calibrateMQ7() {
    float Rs_air = getSensorResistance(MQ7_PIN);
    R0_MQ7 = Rs_air / 27.5;  // 27.5 is the Rs/R0 ratio for CO at 1 ppm
    Serial.print("MQ7 R0: ");
    Serial.println(R0_MQ7);
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

    Serial.println("Calibrating Sensors... Keep in clean air for 1 minute.");
    delay(60000);  // Allow sensor stabilization

    calibrateMQ135();
    calibrateMQ7();
    Serial.println("Calibration Complete!");
}

void loop() {
    // Use R0_MQ135 and R0_MQ7 for pollutant calculations in main code
}
