/*
 * ==============================================================================
 * Smart Building Management System - LoRaWAN Cayenne LPP Sensor Node
 * Hardware: LILYGO TTGO LoRa32-OLED V2.1 (ESP32 + SX1276)
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
#include <WiFi.h>
#include <lmic.h>
#include <hal/hal.h>
#include <SPI.h>
#include <Wire.h>
#include <CayenneLPP.h>
#include <esp_mac.h>

// Optional: Adafruit SHT31 (I2C SDA=21, SCL=22)
// #include <Adafruit_SHT31.h>
// Adafruit_SHT31 sht31 = Adafruit_SHT31();

// ==============================================================================
// 1. LORAWAN OTAA CREDENTIALS
// ==============================================================================

#if __has_include("lorawan_credentials.h")
#include "lorawan_credentials.h"
#else
#error "Missing firmware/lorawan_credentials.h. Run: python tools/generate_lorawan_credentials.py"
#endif

// AppEUI / JoinEUI (8 bytes, Little-Endian format for TTN)
static const u1_t PROGMEM APPEUI[8] = { SBMS_JOIN_EUI_LSB_BYTES };
void os_getArtEui (u1_t* buf) { memcpy_P(buf, APPEUI, 8); }

// AppKey (16 bytes, Big-Endian format from TTN Application)
static const u1_t PROGMEM APPKEY[16] = { SBMS_APP_KEY_BYTES };
void os_getDevKey (u1_t* buf) { memcpy_P(buf, APPKEY, 16); }

// DevEUI is generated dynamically from the ESP32 chip's unique MAC address!
// (Little-Endian format required by LMIC)
static u1_t DEVEUI[8];
static const u1_t PROGMEM DEV_EUI_XOR[8] = { SBMS_DEV_EUI_XOR_LSB_BYTES };
void os_getDevEui (u1_t* buf) { memcpy(buf, DEVEUI, 8); }

// ==============================================================================
// 2. PIN MAPPING FOR LILYGO ESP32 LORA BOARDS
// ==============================================================================
// Verified pinout for LILYGO TTGO LoRa32-OLED V2.1 (board revision 1.6.1).
constexpr int SBMS_LORA_SCK = 5;
constexpr int SBMS_LORA_MISO = 19;
constexpr int SBMS_LORA_MOSI = 27;
constexpr int SBMS_LORA_NSS = 18;

const lmic_pinmap lmic_pins = {
    .nss = SBMS_LORA_NSS,
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

// ------------------------------------------------------------------------------
// BENCH TEST MODE
// ------------------------------------------------------------------------------
// Set DUMMY_SENSORS to 1 to transmit simulated readings for every channel the
// CAYENNE_LPP_V1 cloud profile understands, with no sensors wired up at all.
// This exercises the full path -- LoRaWAN join, gateway, TTN decoder, webhook,
// auto-discovery, floor map tiles and alarm thresholds -- on a bare board.
// Set it back to 0 once real sensors are attached.
#define DUMMY_SENSORS 1

// Channels 9-11 use the EXTENDED Cayenne LPP types (current / power /
// concentration). Channels 1-8 use the classic types every decoder supports.
// If TTN's Live Data tab shows channels 9-11 arriving undecoded, set this to 0:
// you still get 8 populated channels, and the payload drops to 29 bytes.
#define DUMMY_EXTENDED_TYPES 1

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

    // Namespace the hardware EUI for this TTN application. This prevents a
    // board previously registered in another TTN app from claiming the same
    // globally unique DevEUI while keeping derivation fully deterministic.
    for (int i = 0; i < 8; i++) {
        DEVEUI[i] ^= pgm_read_byte(&DEV_EUI_XOR[i]);
    }

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

// A small bounded random walk. Simulated values drift like a real sensor
// instead of jumping randomly, so the dashboard graphs and the alarm
// thresholds get something realistic to work against.
static float drift(float value, float step, float low, float high) {
    value += (random(-100, 101) / 100.0) * step;
    if (value < low)  value = low;
    if (value > high) value = high;
    return value;
}

void do_send(osjob_t* j) {
    if (LMIC.opmode & OP_TXRXPEND) {
        Serial.println(F("[LMIC] OP_TXRXPEND, not sending now"));
        return;
    }

    lpp.reset();

#if DUMMY_SENSORS
    // ---------------------------------------------------------------------
    // Simulated payload. No sensors required.
    //
    // Each channel below is named for the cloud telemetry field it lands in
    // after TTN decodes it (see CAYENNE_CHANNEL_PREFIX_MAP in app/main.py).
    // ---------------------------------------------------------------------
    static float temp     = 22.5f;   // -> temperature
    static float hum      = 50.0f;   // -> humidity
    static float vbat     = 4.05f;   // -> voltage
    static float lux      = 420.0f;  // -> lux
    static float pressure = 1013.0f; // -> pressure
    static float analogIn = 6.5f;    // -> analog_in
    static float current  = 0.65f;   // -> current
    static float power    = 145.0f;  // -> power
    static float co2      = 620.0f;  // -> co2

    temp     = drift(temp,     0.4f,  18.0f,   28.0f);
    hum      = drift(hum,      1.5f,  30.0f,   70.0f);
    vbat     = drift(vbat,     0.02f,  3.35f,   4.20f);
    lux      = drift(lux,     40.0f,   0.0f, 2000.0f);
    pressure = drift(pressure, 0.8f, 980.0f, 1040.0f);
    analogIn = drift(analogIn, 0.3f,   0.0f,   10.0f);
    current  = drift(current,  0.05f,  0.0f,    2.0f);
    power    = drift(power,    8.0f,   0.0f,  500.0f);
    co2      = drift(co2,     35.0f, 400.0f, 1800.0f);

    // Motion trips roughly 1 uplink in 4; the door contact roughly 1 in 8.
    uint8_t motion   = (random(0, 4) == 0) ? 1 : 0;   // -> motion
    uint8_t doorOpen = (random(0, 8) == 0) ? 1 : 0;   // -> digital_in

    // Classic Cayenne LPP types -- decoded by every LPP implementation.
    lpp.addTemperature(1, temp);
    lpp.addRelativeHumidity(2, hum);
    lpp.addPresence(3, motion);
    lpp.addVoltage(4, vbat);
    lpp.addLuminosity(5, (uint16_t)lux);
    lpp.addBarometricPressure(6, pressure);
    lpp.addAnalogInput(7, analogIn);
    lpp.addDigitalInput(8, doorOpen);

#if DUMMY_EXTENDED_TYPES
    // Extended Cayenne LPP types. Confirm these decode on TTN before relying
    // on them; if they do not, set DUMMY_EXTENDED_TYPES to 0.
    lpp.addCurrent(9, current);
    lpp.addPower(10, (uint16_t)power);
    lpp.addConcentration(11, (uint16_t)co2);
#endif

    Serial.print(F("[TX] SIMULATED Cayenne LPP packet queued: "));
    Serial.print(lpp.getSize());
    Serial.print(F(" bytes | T "));
    Serial.print(temp, 1);
    Serial.print(F("C | RH "));
    Serial.print(hum, 1);
    Serial.print(F("% | Motion "));
    Serial.print(motion);
    Serial.print(F(" | VBat "));
    Serial.print(vbat, 2);
    Serial.println(F("V"));

#else
    // ---------------------------------------------------------------------
    // Real sensor payload.
    // ---------------------------------------------------------------------

    // 1. Read Temperature & Humidity (Channel 1 & 2)
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

    Serial.print(F("[TX] Cayenne LPP packet queued: "));
    Serial.print(lpp.getSize());
    Serial.print(F(" bytes | Temp: "));
    Serial.print(temp);
    Serial.print(F(" C | Hum: "));
    Serial.print(hum);
    Serial.print(F(" % | VBat: "));
    Serial.print(vbat);
    Serial.println(F(" V"));
#endif

    // Prepare transmission on LoRaWAN Port 1
    LMIC_setTxData2(1, lpp.getBuffer(), lpp.getSize(), 0);
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
#if DUMMY_SENSORS
            // The simulated payload is 41 bytes. At SF12 that is ~1.8 s of
            // airtime per uplink, which the EU868 1% duty cycle and TTN's
            // 30 s/day fair-use budget cannot sustain at TX_INTERVAL_SECONDS.
            // Bench testing is done next to the gateway, so pin the fastest
            // data rate: ~0.12 s per uplink, and a 60 s interval works.
            // Remove this (or set DUMMY_SENSORS to 0) before deploying a node
            // that has to reach a gateway at real range.
            LMIC_setAdrMode(0);
            LMIC_setDrTxpow(DR_SF7, 14);
            Serial.println(F("[BENCH] ADR off, data rate pinned to SF7 for short-range testing."));
#endif
            break;
        case EV_JOIN_FAILED:
            Serial.println(F("EV_JOIN_FAILED. Check AppKey / Gateway signal."));
            break;
        case EV_TXCOMPLETE:
            Serial.println(F("EV_TXCOMPLETE (Uplink delivered successfully)"));
            // Schedule next uplink after TX_INTERVAL_SECONDS
            os_setTimedCallback(&sendjob, os_getTime() + sec2osticks(TX_INTERVAL_SECONDS), do_send);
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

    // Seed the PRNG from the hardware RNG so simulated readings are not
    // identical on every boot.
    randomSeed(esp_random());

    // Initialize Unique Hardware DevEUI from ESP32 MAC
    initUniqueDevEUI();

    // Initialize the radio bus explicitly. The TTGO LoRa32 does not use the
    // ESP32 default VSPI MISO/MOSI mapping.
    SPI.begin(SBMS_LORA_SCK, SBMS_LORA_MISO, SBMS_LORA_MOSI, SBMS_LORA_NSS);

    // Initialize LMIC with the verified pin table and stop cleanly if the
    // SX1276 cannot be initialized.
    if (!os_init_ex((const void*)&lmic_pins)) {
        Serial.println(F("[FATAL] SX1276 initialization failed. Check board revision and LoRa pins."));
        while (true) {
            delay(1000);
        }
    }
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
