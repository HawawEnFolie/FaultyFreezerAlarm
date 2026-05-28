#include <Arduino.h>
#include <Wire.h> 
#include <SPI.h>  
#include <Adafruit_MAX31865.h>

// - - - - - [ BUFFER & TINYGSM CONFIGURATION ] - - - - -
#define TINY_GSM_RX_BUFFER 1024 
#define TINY_GSM_MODEM_SIM7600 
#include <TinyGsmClient.h>

// - - - - - [ MODEM CONFIGURATION ] - - - - -
#define MODEM_TX 26
#define MODEM_RX 27
#define MODEM_PWRKEY 4
#define MODEM_RST 5
#define MODEM_DTR 25  
#define BAT_EN 12  
#define GSM_PIN "XXXX"

HardwareSerial SerialAT(1);
TinyGsm Modem(SerialAT);

// - - - - - [ PT100 CONFIGURATION ] - - - - -
#define MAX_CS 15
Adafruit_MAX31865 Thermo = Adafruit_MAX31865(MAX_CS);
#define RREF 430.0 
#define RNOMINAL 100.0 

// - - - - - [ ALERT NUMBERS ] - - - - -
const char* ALERT_NUMBERS[] = {
  "+33000000000",
  "+33111111111",
  "+33222222222",
  "+33333333333",
  "+33444444444"
};
String TARGET_FREEZER = "Micro-biology freezer n°2";
const int NUMBER_COUNT = sizeof(ALERT_NUMBERS) / sizeof(ALERT_NUMBERS[0]);

// - - - - - [ THRESHOLDS ] - - - - -
const float CRITICAL_THRESHOLD = -65.0; 
const float TOO_COLD_THRESHOLD = -100.0; 
const float TOO_HOT_THRESHOLD  = 15.0;   

const unsigned long READ_INTERVAL = 10000;
unsigned long lastReadTime = 0;

// - - - - - [ ANTI-SPAM FLAGS ] - - - - -
bool criticalThresholdAlertActive = false;
bool tooColdAlertActive          = false;
bool tooHotAlertActive           = false;

// - - - - - [ POWER ON ] - - - - -
void PowerOnModem() {
  pinMode(BAT_EN, OUTPUT);
  digitalWrite(BAT_EN, HIGH);
  delay(1000); 

  pinMode(MODEM_DTR, OUTPUT);
  digitalWrite(MODEM_DTR, LOW); 

  pinMode(MODEM_RST, OUTPUT);
  digitalWrite(MODEM_RST, HIGH); 
  delay(200);

  pinMode(MODEM_PWRKEY, OUTPUT);
  digitalWrite(MODEM_PWRKEY, HIGH);
  delay(100);
  digitalWrite(MODEM_PWRKEY, LOW);  
  delay(1500);                     
  digitalWrite(MODEM_PWRKEY, HIGH); 

  delay(6000);
}

// - - - - - [ NUMBER ROUTING LOGIC ] - - - - -
bool SendAlertToAll(String message) {
  int successCount = 0;

  for (int i = 0; i < NUMBER_COUNT; i++) {
    if (!Modem.isNetworkConnected()) {
      Modem.waitForNetwork(10000L); 
    }

    if (Modem.sendSMS(ALERT_NUMBERS[i], message)) {
      successCount++;
    }
    delay(1000);
  }
  return successCount > 0;
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n[ INFO ] Starting monitoring program...");

// - - - - - [ PT100 INITIALIZATION ] - - - - -
  Thermo.begin(MAX31865_4WIRE); 
  if (Thermo.readFault()) {
    Serial.println("[ ERROR ] Initial fault detected with PT100 probe.");
    Thermo.clearFault();
  }

// - - - - - [ MODEM SYNCHRONIZATION ] - - - - -
  PowerOnModem();
  SerialAT.begin(115200, SERIAL_8N1, MODEM_RX, MODEM_TX);
  delay(3000);

  if (!Modem.restart()) {
    Serial.println("[ ERROR ] Modem unreachable.");
  } else {
    if (strlen(GSM_PIN) > 0 && Modem.getSimStatus() != 3) {
      Modem.simUnlock(GSM_PIN);
      delay(3000); 
    }

    if (Modem.waitForNetwork(60000L, true)) {
      Serial.println("[ INFO ] Modem connected to the 4G cellular network.");
    } else {
      Serial.println("[ ERROR ] Unable to register on the mobile network.");
    }
  }
  Serial.println("[ INFO ] Real-time monitoring started.");
}

void loop() {
  if (millis() - lastReadTime >= READ_INTERVAL) {
    lastReadTime = millis();

    uint16_t rtd = Thermo.readRTD();
    float Temperature = Thermo.temperature(RNOMINAL, RREF);

    if (Thermo.readFault()) {
      Serial.println("[ ERROR ] Fault or disconnection on PT100 probe! Reading cancelled.");
      Thermo.clearFault();
      return;
    }

    Serial.print("[ INFO ] Temperature: ");
    Serial.print(Temperature);
    Serial.println(" °C");

// - - - - - [ TOO COLD ] - - - - -
    if (Temperature < TOO_COLD_THRESHOLD) {
      if (!tooColdAlertActive) {
        String msg = "ALERT '" + TARGET_FREEZER + "': Abnormally LOW temperature at " + String(Temperature, 2) + " C.";
        if (SendAlertToAll(msg)) tooColdAlertActive = true;
      }
    } else {
      if (tooColdAlertActive) {
        tooColdAlertActive = false; // Rearm
      }
    }

// - - - - - [ TOO HOT ] - - - - -
    if (Temperature > TOO_HOT_THRESHOLD) {
      if (!tooHotAlertActive) {
        String msg = "MAJOR ALERT '" + TARGET_FREEZER + "': Freezer stopped probe taked out! Temperature at " + String(Temperature, 2) + " C!";
        if (SendAlertToAll(msg)) tooHotAlertActive = true;
      }
    } else {
      if (tooHotAlertActive) {
        tooHotAlertActive = false; // Rearm
      }
    }

// - - - - - [ CRITICAL THRESHOLD ] - - - - -
    if (Temperature > CRITICAL_THRESHOLD && Temperature <= TOO_HOT_THRESHOLD) {
      if (!criticalThresholdAlertActive) {
        String msg = "ALERT '" + TARGET_FREEZER + "': Critical temperature detected at " + String(Temperature, 2) + " C!";
        if (SendAlertToAll(msg)) criticalThresholdAlertActive = true; 
      }
    } else {
      if (Temperature <= CRITICAL_THRESHOLD && criticalThresholdAlertActive) {
        criticalThresholdAlertActive = false; // Rearm
      }
    }
  }
}
