/*
 * ==============================================================================
 * Smart Building Management System - LoRaWAN Cayenne LPP Sensor Node
 * Hardware: LILYGO T-Beam / T-Call / ESP32 + SX1262 / SX1276 LoRa Transceiver
 * ==============================================================================
 *
 * FEATURES:
 *  1. 100% Zero-Touch: LoRaWAN only (Wi-Fi is completely disabled for long battery life).
 *  2. Auto-Generated DevEUI: Derived from ESP32 factory MAC address. Every board
 *     automatically gets a globally unique DevEUI!
 *  3. Cayenne LPP Encoding: Uses universal Cayenne Low Power Payload. TTN and the
 *     Smart Building Cloud decode all sensor values automatically with zero decoder code!
 *  4. Cloud Auto-Discovery: The moment this device transmits, it appears in the
 *     "Discovered Devices" inbox on the Cloud Map Editor.
 *
 * REQUIRED ARDUINO LIBRARIES (Install via Arduino Library Manager):
 *  - "MCCI LoRaWAN LMIC library" by IBM, Matthijs Kooijman, Terry Moore
 *  - "CayenneLPP" by ElectronicCats
 *  - "Adafruit SHT31 Library" (Optional, for SHT30/SHT31 Temp & Humidity)
 * ==============================================================================
 */

#include <Arduino.h>
#include <lmic.h>
#include <hal/hal.h>
#include <SPI.h>
#include <Wire.h>
#include <CayenneLPP.h>
#include <esp_wifi.h> // Used to cleanly power down the Wi-Fi radio

// Optional: Adafruit SHT31 (I2C SDA=21, SCL=22)
// #include <Adafruit_SHT31.h>
// Adafruit_SHT31 sht31 = Adafruit_SHT31();

// ==============================================================================
// 1. LORAWAN OTAA CREDENTIALS
// ==============================================================================

// AppEUI / JoinEUI (8 bytes, Little-Endian format for TTN)
// Example: 00 00 00 00 00 00 00 00
static const u1_t PROGMEM APPEUI[8] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
void os_getArtEui (u1_t* buf) { memcpy_P(buf, APPEUI, 8); }

// AppKey (16 bytes, Big-Endian format from TTN Application)
// Paste your 16-byte TTN Application Root Key here:
static const u1_t PROGMEM APPKEY[16] = {
    0x2B, 0x7E, 0x15, 0x16, 0x28, 0xAE, 0xD2, 0xA6,
    0xAB, 0xF7, 0x15, 0x88, 0x09, 0xCF, 0x4F, 0x3C
};
void os_getDevKey (u1_t* buf) { memcpy_P(buf, APPKEY, 16); }

// DevEUI is generated dynamically from the ESP32 chip's unique MAC address!
// (Little-Endian format required by LMIC)
static u1_t DEVEUI[8];
void os_getDevEui (u1_t* buf) { memcpy(buf, DEVEUI, 8); }

// ==============================================================================
// 2. PIN MAPPING FOR LILYGO ESP32 LORA BOARDS
// ==============================================================================
// Standard pinout for LILYGO TTGO T-Beam and ESP32 LoRa32 v1/v2:
const lmic_pinmap lmic_pins = {
    .nss = 18,
    .rxtx = LMIC_UNUSED_PIN,
    .rst = 23, // Use 14 on some T-Beam revisions
    .dio = {26, 33, 32},
};

// ==============================================================================
// 3. HARDWARE CONFIGURATION & INTERVALS
// ==============================================================================
const unsigned TX_INTERVAL_SECONDS = 60; // Uplink interval (e.g. 60 to 300 seconds)
static osjob_t sendjob;
CayenneLPP lpp(51); // 51 bytes buffer

#define PIN_PIR_MOTION  13  // Motion or door contact digital input
#define PIN_BATTERY_ADC 35  // Battery ADC voltage divider pin

void initUniqueDevEUI() {
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);

    // Form an IEEE EUI-64: [MAC0, MAC1, MAC2, 0xFF, 0xFE, MAC3, MAC4, MAC5]
    // Stored Little-Endian for LMIC:
    DEVEUI[0] = mac[5];
    DEVEUI[1] = mac[4];
    DEVEUI[2] = mac[3];
    DEVEUI[3] = 0xFE;
    DEVEUI[4] = 0xFF;
    DEVEUI[5] = mac[2];
    DEVEUI[6] = mac[1];
    DEVEUI[7] = mac[0];

    Serial.print(F("[INFO] Unique Hardware DevEUI (MSB): "));
    for (int i = 7; i >= 0; i--) {
        if (DEVEUI[i] < 0x10) Serial.print("0");
        Serial.print(DEVEUI[i], HEX);
        if (i > 0) Serial.print(":");
    }
    Serial.println();
}

float readBatteryVoltage() {
    // 1:1 voltage divider (100k / 100k) on ESP32 ADC
    int raw = analogRead(PIN_BATTERY_ADC);
    float voltage = ((float)raw / 4095.0) * 3.3 * 2.0;
    if (voltage < 2.0 || voltage > 4.5) {
        voltage = 3.85; // Simulated fallback if pin is floating
    }
    return voltage;
}

void do_send(osjob_t* j) {
    if (LMIC.opmode & OP_TXRXPEND) {
        Serial.println(F("[LMIC] OP_TXRXPEND, not sending now"));
    } else {
        lpp.reset();

        // 1. Read / Simulate Temperature & Humidity (Channel 1 & 2)
        // If SHT31 is connected: float t = sht31.readTemperature(); float h = sht31.readHumidity();
        float temp = 22.5 + (random(-15, 20) / 10.0);
        float hum  = 50.0 + (random(-20, 20) / 10.0);
        lpp.addTemperature(1, temp);
        lpp.addRelativeHumidity(2, hum);

        // 2. Read PIR Motion / Presence (Channel 3)
        bool motion = (digitalRead(PIN_PIR_MOTION) == HIGH);
        lpp.addPresence(3, motion ? 1 : 0);

        // 3. Read Battery Voltage (Channel 4)
        float vbat = readBatteryVoltage();
        lpp.addVoltage(4, vbat);

        // Prepare transmission on LoRaWAN Port 1
        LMIC_setTxData2(1, lpp.getBuffer(), lpp.getSize(), 0);

        Serial.print(F("[TX] Cayenne LPP packet queued: "));
        Serial.print(lpp.getSize());
        Serial.print(F(" bytes | Temp: "));
        Serial.print(temp);
        Serial.print(F(" C | Hum: "));
        Serial.print(hum);
        Serial.print(F(" % | VBat: "));
        Serial.print(vbat);
        Serial.println(F(" V"));
    }
}

void onEvent (ev_t ev) {
    Serial.print(F("[LMIC Event] "));
    Serial.print(os_getTime());
    Serial.print(F(": "));
    switch(ev) {
        case EV_JOINING:
            Serial.println(F("EV_JOINING (Sending OTAA Join Request over LoRa...)"));
            break;
        case EV_JOINED:
            Serial.println(F("EV_JOINED! Device is connected to LoRaWAN Gateway!"));
            // Disable link check validation once joined
            LMIC_setLinkCheckMode(0);
            break;
        case EV_JOIN_FAILED:
            Serial.println(F("EV_JOIN_FAILED. Check AppKey / Gateway signal."));
            break;
        case EV_TXCOMPLETE:
            Serial.println(F("EV_TXCOMPLETE (Uplink delivered successfully)"));
            // Schedule next uplink after TX_INTERVAL_SECONDS
            os_setTimedCallback(&sendjob, os_getTime() + sec2ostime(TX_INTERVAL_SECONDS), do_send);
            break;
        case EV_RESET:
            Serial.println(F("EV_RESET"));
            break;
        case EV_RXCOMPLETE:
            Serial.println(F("EV_RXCOMPLETE"));
            break;
        default:
            Serial.print(F("Unknown event: "));
            Serial.println((unsigned) ev);
            break;
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println(F("\n======================================================="));
    Serial.println(F("  Smart Building Management System - LoRaWAN Node"));
    Serial.println(F("======================================================="));

    // Disable Wi-Fi and Bluetooth radios completely to conserve battery
    WiFi.mode(WIFI_OFF);
    btStop();
    Serial.println(F("[INFO] Wi-Fi & Bluetooth turned OFF (Pure LoRa Mode)"));

    pinMode(PIN_PIR_MOTION, INPUT_PULLDOWN);

    // Initialize Unique Hardware DevEUI from ESP32 MAC
    initUniqueDevEUI();

    // Initialize LMIC OS
    os_init();
    LMIC_reset();

    // Optional: Relax clock tolerance for ESP32 internal RC oscillator
    LMIC_setClockError(MAX_CLOCK_ERROR * 10 / 100);

    // Start OTAA Join and initial transmission
    Serial.println(F("[INFO] Starting LoRaWAN transmission..."));
    do_send(&sendjob);
}

void loop() {
    os_runloop_once();
}
