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
 *  - "CayenneLPP" by ElectronicCats (v1.1+, for the extended LPP types)
 *  - "Adafruit SSD1306" and "Adafruit GFX Library" (onboard OLED)
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
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

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
// Bench testing: 30 s so changes show up quickly. The 25-byte payload is
// ~62 ms of airtime at SF7, so 30 s is 0.21% duty cycle -- well inside the
// EU868 1% limit. Raise to 300+ for a deployed battery node, and note that
// The Things Network's public cloud fair-use budget (30 s airtime/day)
// would not tolerate this rate; a local stack has no such limit.
const unsigned TX_INTERVAL_SECONDS = 30;
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

// Cayenne LPP defines more data types than most decoders implement. The
// Things Stack's built-in decoder handles only the standard set, and it
// rejects the WHOLE payload -- logging "cayennelpp: invalid output" and
// producing no decoded_payload at all -- if it meets even one type it does not
// know. It is not a partial decode.
//
// Setting this to 1 adds voltage, current, power and concentration. Leave it
// at 0 for The Things Stack's built-in formatter; turn it on only with a
// decoder you have confirmed supports them (a custom JavaScript formatter, or
// ChirpStack).
#define DUMMY_EXTENDED_TYPES 0

#define PIN_PIR_MOTION  13  // Motion or door contact digital input
#define PIN_BATTERY_ADC 35  // Battery ADC voltage divider pin

// ------------------------------------------------------------------------------
// ONBOARD OLED (SSD1306 128x64 over I2C)
// ------------------------------------------------------------------------------
// Set to 0 to compile the display out entirely.
#define ENABLE_OLED 1

#define OLED_WIDTH   128
#define OLED_HEIGHT   64
#define OLED_ADDRESS 0x3C  // Standard address for the TTGO onboard SSD1306
#define OLED_SDA       21  // ESP32 default I2C pins, which this board uses
#define OLED_SCL       22
#define OLED_RESET     -1  // No dedicated reset line on this board

#if ENABLE_OLED
Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, OLED_RESET);
static bool oledReady = false;

// Snapshot of what the screen should show. Written from the LMIC callbacks and
// from do_send(), which must stay fast -- rendering happens later, in loop().
static char     devEuiText[17] = "................";
static const char *joinState   = "BOOTING";
static uint32_t uplinkCount    = 0;
static uint16_t lastPayloadLen = 0;
static float    lastTemp       = 0.0f;
static float    lastHum        = 0.0f;
static float    lastVbat       = 0.0f;
static bool     displayDirty   = true;
#endif

bool initUniqueDevEUI() {
    uint8_t mac[6];
    if (esp_read_mac(mac, ESP_MAC_WIFI_STA) != ESP_OK) {
        Serial.println(F("[FATAL] Could not read the ESP32 hardware MAC; DevEUI was not generated."));
        return false;
    }

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

#if ENABLE_OLED
    // Same MSB order as the serial line, without separators so all 16 hex
    // characters fit one 21-character OLED row. This is the value you register
    // in The Things Stack, so showing it on screen saves needing a serial cable.
    for (int i = 0; i < 8; i++) {
        snprintf(&devEuiText[i * 2], 3, "%02X", DEVEUI[7 - i]);
    }
    displayDirty = true;
#endif
    return true;
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

#if ENABLE_OLED
// EU868 maps DR0..DR5 onto SF12..SF7.
static uint8_t currentSpreadingFactor() {
    uint8_t dr = LMIC.datarate;
    return (dr <= 5) ? (12 - dr) : 0;
}

// Redraw the status screen. Called only from loop(), never from an LMIC
// callback: pushing the 1 KB framebuffer over I2C takes long enough that doing
// it inside a callback risks missing an RX window.
static void renderDisplay() {
    if (!oledReady) return;

    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);

    display.setCursor(0, 0);
    display.println(F("SBMS LoRaWAN Node"));
    display.drawFastHLine(0, 10, OLED_WIDTH, SSD1306_WHITE);

    // The DevEUI you need in order to register this board.
    display.setCursor(0, 14);
    display.print(F("EUI "));
    display.println(devEuiText);

    display.setCursor(0, 25);
    display.print(F("State "));
    display.println(joinState);

    display.setCursor(0, 35);
    display.print(F("TX "));
    display.print(uplinkCount);
    display.print(F("  "));
    display.print(lastPayloadLen);
    display.print(F("B"));
    uint8_t sf = currentSpreadingFactor();
    if (sf) {
        display.print(F("  SF"));
        display.print(sf);
    }

    display.drawFastHLine(0, 45, OLED_WIDTH, SSD1306_WHITE);

    display.setCursor(0, 49);
    display.print(lastTemp, 1);
    display.print(F("C "));
    display.print(lastHum, 0);
    display.print(F("% "));
    display.print(lastVbat, 2);
    display.print(F("V"));

#if DUMMY_SENSORS
    display.setCursor(0, 57);
    display.print(F("SIMULATED DATA"));
#endif

    display.display();
}
#endif

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
#if DUMMY_EXTENDED_TYPES
    static float current  = 0.65f;   // -> current
    static float power    = 145.0f;  // -> power
    static float co2      = 620.0f;  // -> co2
#endif

    temp     = drift(temp,     0.4f,  18.0f,   28.0f);
    hum      = drift(hum,      1.5f,  30.0f,   70.0f);
    vbat     = drift(vbat,     0.02f,  3.35f,   4.20f);
    lux      = drift(lux,     40.0f,   0.0f, 2000.0f);
    pressure = drift(pressure, 0.8f, 980.0f, 1040.0f);
    analogIn = drift(analogIn, 0.3f,   0.0f,   10.0f);
#if DUMMY_EXTENDED_TYPES
    current  = drift(current,  0.05f,  0.0f,    2.0f);
    power    = drift(power,    8.0f,   0.0f,  500.0f);
    co2      = drift(co2,     35.0f, 400.0f, 1800.0f);
#endif

    // Motion trips roughly 1 uplink in 4; the door contact roughly 1 in 8.
    uint8_t motion   = (random(0, 4) == 0) ? 1 : 0;   // -> motion
    uint8_t doorOpen = (random(0, 8) == 0) ? 1 : 0;   // -> digital_in

    // Standard Cayenne LPP types. Every decoder implements these, including
    // The Things Stack's built-in one. 25 bytes total.
    lpp.addTemperature(1, temp);
    lpp.addRelativeHumidity(2, hum);
    lpp.addPresence(3, motion);
    lpp.addLuminosity(5, (uint16_t)lux);
    lpp.addBarometricPressure(6, pressure);
    lpp.addAnalogInput(7, analogIn);
    lpp.addDigitalInput(8, doorOpen);

#if DUMMY_EXTENDED_TYPES
    // Extended types. Channel 4 is battery voltage, which is as unsupported by
    // the built-in decoder as channels 9-11 are, so it lives here rather than
    // above. Adds 16 bytes.
    lpp.addVoltage(4, vbat);
    lpp.addCurrent(9, current);
    lpp.addPower(10, (uint16_t)power);
    lpp.addConcentration(11, (uint16_t)co2);
#endif

#if ENABLE_OLED
    lastTemp = temp;
    lastHum  = hum;
    lastVbat = vbat;
    lastPayloadLen = lpp.getSize();
    displayDirty = true;
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

#if ENABLE_OLED
    lastTemp = temp;
    lastHum  = hum;
    lastVbat = vbat;
    lastPayloadLen = lpp.getSize();
    displayDirty = true;
#endif

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
#if ENABLE_OLED
            joinState = "JOINING";
            displayDirty = true;
#endif
            break;
        case EV_JOINED:
            Serial.println(F("EV_JOINED! Device is connected to LoRaWAN Gateway!"));
            // Disable link check validation once joined
            LMIC_setLinkCheckMode(0);
#if DUMMY_SENSORS
            // The simulated payload is 25 bytes (41 with extended types). At
            // SF12 even the smaller one is ~1.2 s of
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
#if ENABLE_OLED
            joinState = "JOINED";
            displayDirty = true;
#endif
            break;
        case EV_JOIN_FAILED:
            Serial.println(F("EV_JOIN_FAILED. Check AppKey / Gateway signal."));
#if ENABLE_OLED
            joinState = "JOIN FAIL";
            displayDirty = true;
#endif
            break;
        case EV_JOIN_TXCOMPLETE:
            // The join request went out but no join-accept came back. This is
            // the useful one: it separates "no gateway heard me" from "a
            // gateway heard me but the JoinEUI/AppKey did not match".
            Serial.println(F("EV_JOIN_TXCOMPLETE (Join request sent, no JoinAccept received)"));
#if ENABLE_OLED
            joinState = "NO ACCEPT";
            displayDirty = true;
#endif
            break;
        case EV_TXSTART:
            // Fired by MCCI LMIC as the radio keys up, once per uplink. Not an
            // error -- it simply has no case in most example sketches, which is
            // why it shows up as "Unknown event: 17".
            Serial.println(F("EV_TXSTART (Radio transmitting...)"));
            break;
        case EV_TXCANCELED:
            // A queued transmission was dropped before it went out, usually
            // because the duty-cycle budget for the sub-band was exhausted.
            Serial.println(F("EV_TXCANCELED (Transmission aborted before sending)"));
            break;
        case EV_RXSTART:
            // Fires twice per uplink, opening the RX1 and RX2 windows. Comment
            // this line out if it makes the serial log too noisy.
            Serial.println(F("EV_RXSTART (Opening receive window)"));
            break;
        case EV_TXCOMPLETE:
            Serial.println(F("EV_TXCOMPLETE (Uplink delivered successfully)"));
#if ENABLE_OLED
            uplinkCount++;
            joinState = "ONLINE";
            displayDirty = true;
#endif
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

#if ENABLE_OLED
    // Bring the screen up before anything else can fail, so a fatal error in
    // setup() is visible without a serial cable attached.
    Wire.begin(OLED_SDA, OLED_SCL);
    oledReady = display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDRESS,
                              /*reset=*/true, /*periphBegin=*/false);
    if (!oledReady) {
        Serial.println(F("[WARN] SSD1306 not found; continuing without the display."));
    } else {
        display.clearDisplay();
        display.setTextSize(1);
        display.setTextColor(SSD1306_WHITE);
        display.setCursor(0, 0);
        display.println(F("SBMS LoRaWAN Node"));
        display.println();
        display.println(F("Starting up..."));
        display.display();
    }
#endif

    // Disable Wi-Fi and Bluetooth radios completely to conserve battery
    WiFi.mode(WIFI_OFF);
    btStop();
    Serial.println(F("[INFO] Wi-Fi & Bluetooth turned OFF (Pure LoRa Mode)"));

    pinMode(PIN_PIR_MOTION, INPUT_PULLDOWN);

    // Seed the PRNG from the hardware RNG so simulated readings are not
    // identical on every boot.
    randomSeed(esp_random());

    // Initialize Unique Hardware DevEUI from ESP32 MAC
    if (!initUniqueDevEUI()) {
        while (true) {
            delay(1000);
        }
    }

    // Initialize the radio bus explicitly. The TTGO LoRa32 does not use the
    // ESP32 default VSPI MISO/MOSI mapping.
    SPI.begin(SBMS_LORA_SCK, SBMS_LORA_MISO, SBMS_LORA_MOSI, SBMS_LORA_NSS);

    // Initialize LMIC with the verified pin table and stop cleanly if the
    // SX1276 cannot be initialized.
    if (!os_init_ex((const void*)&lmic_pins)) {
        Serial.println(F("[FATAL] SX1276 initialization failed. Check board revision and LoRa pins."));
#if ENABLE_OLED
        if (oledReady) {
            display.clearDisplay();
            display.setCursor(0, 0);
            display.println(F("LoRa INIT FAILED"));
            display.println();
            display.println(F("Check board revision"));
            display.println(F("and SX1276 pins."));
            display.display();
        }
#endif
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

#if ENABLE_OLED
    // Refresh at most every 250 ms, and never while a transmission or receive
    // window is pending -- os_runloop_once() has to be serviced promptly, and
    // the I2C framebuffer push is comparatively slow.
    static unsigned long lastRender = 0;
    if (displayDirty && !(LMIC.opmode & OP_TXRXPEND)
        && (millis() - lastRender) > 250) {
        lastRender = millis();
        displayDirty = false;
        renderDisplay();
    }
#endif
}
