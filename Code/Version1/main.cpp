#include <Arduino.h>
#include <Wire.h> 
#include <SPI.h>  
#include <Adafruit_MAX31865.h>
#include <Adafruit_GFX.h>       
#include <Adafruit_SSD1306.h>   
#include <driver/rtc_io.h> // Requis pour piloter les résistances du domaine RTC en sommeil

// - - - - - [ BUFFER & TINYGSM CONFIGURATION ] - - - - -
#define TINY_GSM_RX_BUFFER 1024 
#define TINY_GSM_MODEM_SIM7600 
#include <TinyGsmClient.h>

// - - - - - [ MODEM HARDWARE CONFIGURATION ] - - - - -
#define MODEM_TX     26
#define MODEM_RX     27
#define MODEM_PWRKEY 4
#define MODEM_RST     5
#define MODEM_DTR     25  
#define BAT_EN        12  
#define GSM_PIN      "4545"

HardwareSerial SerialAT(1);
TinyGsm Modem(SerialAT);

// - - - - - [ PT100 PROBE CONFIGURATION ] - - - - -
#define MAX_CS       15
Adafruit_MAX31865 Thermo = Adafruit_MAX31865(MAX_CS);
#define RREF         430.0 
#define RNOMINAL     100.0 

// - - - - - [ NAVIGATION BUTTON CONFIGURATION ] - - - - -
#define BUTTON_PIN   14  // Wakeup pin EXT0 (Button <-> GND)

// - - - - - [ BATTERY ADC PIN CONFIGURATION ] - - - - -
#define BAT_ADC_PIN  35  // GPIO 35 (Pont diviseur du schéma)

// - - - - - [ OLED SCREEN CONFIGURATION ] - - - - -
#define SCREEN_WIDTH 128        
#define SCREEN_HEIGHT 64        
#define OLED_RESET    -1        
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET); 

// - - - - - [ DETECTION THRESHOLDS ] - - - - -
const float CRITICAL_THRESHOLD = 30.0;
const float TOO_COLD_THRESHOLD = -100.0;
const float TOO_HOT_THRESHOLD = 65.0;
const float LOW_BATTERY_THRESHOLD = 3.40; 

// - - - - - [ RTC MEMORY VARIABLES (SURVIVES DEEP SLEEP) ] - - - - -
RTC_DATA_ATTR float minTemp = 999.0;
RTC_DATA_ATTR float maxTemp = -999.0;
RTC_DATA_ATTR bool isMinMaxInitialized = false;
RTC_DATA_ATTR bool criticalAlertTriggered = false;
RTC_DATA_ATTR bool tooColdAlertTriggered = false;
RTC_DATA_ATTR bool tooHotAlertTriggered = false;
RTC_DATA_ATTR bool lowBatteryAlertTriggered = false; 
RTC_DATA_ATTR int currentMenuInt = 0; 

// - - - - - [ DEEP SLEEP TIME CONFIGURATION ] - - - - -
#define TIME_TO_SLEEP  60  // Durée du sommeil en mode passif (Seconds)

// Volatile variables (lost at each deep sleep cycle)
float currentTemperature = 0.0;
float currentBatteryVoltage = 4.0; 
bool isProbeFaulty = false;
bool isDiagRunning = false;
bool isModemDiagOK = false;
bool isSimDiagOK = false;
bool isScreenActive = false; 
bool isAlertModeActive = false; 
unsigned long lastActionTime = 0;
const unsigned long SCREEN_TIMEOUT = 15000; 

const char* ALERT_NUMBERS[] = {
  "+33000000000", 
  "+33000000000", 
  "+33000000000", 
  "+33000000000", 
  "+33000000000"  
};
String TARGET_FREEZER = "ARN freezer in cold room";
const int NUMBERS_COUNT = sizeof(ALERT_NUMBERS) / sizeof(ALERT_NUMBERS[0]);

enum Menu { TEMPERATURE, MIN_MAX, THRESHOLDS, DIAGNOSTIC, TEST_SMS, REBOOT, BATTERY };

// Prototypes
void updateDisplay();
bool sendAlertToAll(String message);
void turnOnModem();
void turnOffModem();
void enterDeepSleep();
void readProbe();

// - - - - - [ MODEM POWER MANAGEMENT ] - - - - -
void turnOnModem() {
  Serial.println("[MONITOR - MODEM] Setting control pins output state...");
  pinMode(MODEM_PWRKEY, OUTPUT);
  pinMode(MODEM_RST, OUTPUT);
  pinMode(MODEM_DTR, OUTPUT);
  digitalWrite(MODEM_PWRKEY, HIGH);
  digitalWrite(MODEM_RST, HIGH);
  digitalWrite(MODEM_DTR, LOW); 

  Serial.println("[MONITOR - MODEM] Activating hardware power regulator (BAT_EN = HIGH)...");
  pinMode(BAT_EN, OUTPUT);
  digitalWrite(BAT_EN, HIGH);
  delay(1000); 

  Serial.println("[MONITOR - MODEM] Sending PWRKEY startup pulse...");
  digitalWrite(MODEM_PWRKEY, LOW);  
  delay(1500);                     
  digitalWrite(MODEM_PWRKEY, HIGH); 

  Serial.println("[MONITOR - MODEM] Opening hardware UART1 serial port at 115200 baud...");
  SerialAT.begin(115200, SERIAL_8N1, MODEM_RX, MODEM_TX);
  delay(5000); 
}

void turnOffModem() {
  Serial.println("[MONITOR - MODEM] Sending software power off command to SIM7600...");
  Modem.poweroff();
  delay(500);
  
  Serial.println("[MONITOR - MODEM] Closing UART1 serial port...");
  SerialAT.end();
  
  Serial.println("[MONITOR - MODEM] Cutting power regulator (BAT_EN = LOW)...");
  digitalWrite(BAT_EN, LOW); 
  
  Serial.println("[MONITOR - MODEM] Isolating pins to INPUT to block parasite leaks...");
  pinMode(MODEM_TX, INPUT);
  pinMode(MODEM_RX, INPUT);
  pinMode(MODEM_PWRKEY, INPUT);
  pinMode(MODEM_RST, INPUT);
  pinMode(MODEM_DTR, INPUT);
}

// - - - - - [ SMS SENDING LOGIC ] - - - - -
bool sendAlertToAll(String message) {
  int successCount = 0;
  turnOnModem();
  
  Serial.println("[MONITOR - SMS] Checking modem communication...");
  if (!Modem.restart()) {
    Serial.println("[MONITOR - SMS] ERROR: Modem not responding to AT commands.");
    turnOffModem();
    return false;
  }
  
  if (strlen(GSM_PIN) > 0 && Modem.getSimStatus() != 3) {
    Serial.println("[MONITOR - SMS] Unlocking SIM card...");
    Modem.simUnlock(GSM_PIN);
    delay(3000); 
  }
  
  Serial.println("[MONITOR - SMS] Connecting to 4G cellular network (Max 60s)...");
  if (Modem.waitForNetwork(60000L, true)) {
    Serial.println("[MONITOR - SMS] Network connected. Starting dispatch...");
    for (int i = 0; i < NUMBERS_COUNT; i++) {
      Serial.print("[MONITOR - SMS] Sending to "); Serial.print(ALERT_NUMBERS[i]);
      if (Modem.sendSMS(ALERT_NUMBERS[i], message)) {
        successCount++;
        Serial.println(" -> SUCCESS");
      } else {
        Serial.println(" -> FAILED");
      }
      delay(1000);
    }
  } else {
    Serial.println("[MONITOR - SMS] CRITICAL ERROR: Network signal attachment failed.");
  }
  
  turnOffModem();
  return successCount > 0;
}

// - - - - - [ COMBINED SENSOR & BATTERY READ LOGIC ] - - - - -
void readProbe() {
  uint16_t rtd = Thermo.readRTD();
  currentTemperature = Thermo.temperature(RNOMINAL, RREF);

  if (Thermo.readFault()) {
    Serial.println("[MONITOR - SENSOR] /!\\ ERROR: Fault or open circuit on PT100 probe!");
    isProbeFaulty = true;
    Thermo.clearFault();
  } else {
    isProbeFaulty = false;
    if (!isMinMaxInitialized) {
      minTemp = currentTemperature;
      maxTemp = currentTemperature;
      isMinMaxInitialized = true;
    } else {
      if (currentTemperature < minTemp) minTemp = currentTemperature;
      if (currentTemperature > maxTemp) maxTemp = currentTemperature;
    }
  }

  uint32_t sumMilliVolts = 0;
  const int NUM_SAMPLES = 10;
  for (int i = 0; i < NUM_SAMPLES; i++) {
    sumMilliVolts += analogReadMilliVolts(BAT_ADC_PIN); 
    delay(2);
  }
  float avgMilliVolts = (float)sumMilliVolts / NUM_SAMPLES;
  currentBatteryVoltage = (avgMilliVolts / 1000.0) * 2.0; 
}

void setup() {
  // CORRECTIF 1 : Libérer immédiatement le loquet de la broche BAT_EN appliqué pendant la veille
  gpio_hold_dis((gpio_num_t)BAT_EN);

  Serial.begin(115200);
  delay(500);
  Serial.println("\n==================================================");
  Serial.println("[MONITOR - BOOT] ESP32 Boot/Wakeup detected.");
  
  if (currentMenuInt > BATTERY || currentMenuInt < TEMPERATURE) {
    currentMenuInt = TEMPERATURE;
  }

  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(BAT_ADC_PIN, INPUT);

  Thermo.begin(MAX31865_4WIRE);

  esp_sleep_wakeup_cause_t wakeup_reason = esp_sleep_get_wakeup_cause();

  readProbe(); 
  if(!isProbeFaulty) {
    Serial.print("[MONITOR - METRIC] Current Temperature: "); Serial.print(currentTemperature); Serial.println(" C");
  }

  if (currentBatteryVoltage > 2.0 && currentBatteryVoltage < LOW_BATTERY_THRESHOLD && !lowBatteryAlertTriggered) {
    Serial.println("[MONITOR - ALERT] Tension batterie faible ! Envoi SMS...");
    if (sendAlertToAll("[!] ALERTE BATTERIE FAIBLE : " + String(currentBatteryVoltage, 2) + "V.")) {
      lowBatteryAlertTriggered = true; 
    }
  } else if (currentBatteryVoltage >= (LOW_BATTERY_THRESHOLD + 0.20) || currentBatteryVoltage <= 2.0) {
    lowBatteryAlertTriggered = false;
  }

  // --- CHECK FOR TEMPERATURE ANOMALIES ---
  bool anomalyDetected = false;
  if (!isProbeFaulty) {
    if (currentTemperature < TOO_COLD_THRESHOLD || currentTemperature > TOO_HOT_THRESHOLD || currentTemperature > CRITICAL_THRESHOLD) {
      anomalyDetected = true;
    }
  }

  if (anomalyDetected) {
    Serial.println("[MONITOR - ALERT] CRITICAL STATUS! Locking system into Forced Awake Mode.");
    isAlertModeActive = true; 

    Wire.begin(21, 22);
    if(display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
      display.ssd1306_command(SSD1306_DISPLAYON);
      
      for(int i = 0; i < 4; i++) {
        display.clearDisplay();
        display.invertDisplay(true);
        display.setTextSize(1); display.setCursor(5, 12); display.println("CRITICAL TEMPERATURE");
        display.setTextSize(2); display.setCursor(25, 36); display.print(currentTemperature, 1); display.print("C");
        display.display();
        delay(200);
        display.invertDisplay(false);
        display.display();
        delay(200);
      }
      
      display.clearDisplay();
      display.setTextSize(1);
      display.setCursor(0, 15); display.println("CRITICAL ANOMALY!");
      display.setCursor(0, 35); display.println("Waking up 4G Modem...");
      display.println("Sending SMS alerts...");
      display.display();
    }

    if (currentTemperature < TOO_COLD_THRESHOLD && !tooColdAlertTriggered) {
      if (sendAlertToAll("[!] CRITICAL FROID EXTREME: " + String(currentTemperature, 1) + "C")) tooColdAlertTriggered = true;
    } 
    if (currentTemperature > TOO_HOT_THRESHOLD && !tooHotAlertTriggered) {
      if (sendAlertToAll("[!] CRITICAL CHALEUR EXTREME: " + String(currentTemperature, 1) + "C")) tooHotAlertTriggered = true;
    } 
    if (currentTemperature > CRITICAL_THRESHOLD && currentTemperature <= TOO_HOT_THRESHOLD && !criticalAlertTriggered) {
      if (sendAlertToAll("[!] CRITICAL THRESHOLD EXCEEDED: " + String(currentTemperature, 1) + "C")) criticalAlertTriggered = true;
    }
  } 
  else {
    if (wakeup_reason == ESP_SLEEP_WAKEUP_EXT0) {
      Serial.println("[MONITOR - WAKEUP] Triggered by user button. UI interface enabled.");
      isScreenActive = true;
      lastActionTime = millis();

      Wire.begin(21, 22);
      if(display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        display.ssd1306_command(SSD1306_DISPLAYON);
        updateDisplay();
      }
    } 
    else {
      Serial.println("[MONITOR - ECO] Cyclic routine check (Timer). Everything nominal. Sleeping.");
      enterDeepSleep();
    }
  }
}

void loop() {
  if (isAlertModeActive) {
    static unsigned long lastFlashTime = 0;
    static unsigned long lastCrisisMeasureTime = 0;
    static bool flashState = false;

    if (millis() - lastFlashTime >= 400) {
      lastFlashTime = millis();
      flashState = !flashState;
      
      display.clearDisplay();
      display.invertDisplay(flashState);
      display.setTextColor(SSD1306_WHITE);
      
      display.setTextSize(1);
      display.setCursor(5, 12);
      display.println("TEMPERATURE CRITIQUE");
      
      display.setTextSize(2);
      display.setCursor(25, 36);
      display.print(currentTemperature, 1);
      display.write(247); 
      display.print("C");
      display.display();
    }

    if (millis() - lastCrisisMeasureTime >= 5000) {
      lastCrisisMeasureTime = millis();
      readProbe();
      Serial.print("[MONITOR - CRISIS] Fast check loop (5s) -> Temp: ");
      Serial.print(currentTemperature); Serial.println(" C");

      if (!isProbeFaulty && currentTemperature <= CRITICAL_THRESHOLD) {
        Serial.println("[MONITOR - ALERT] Temperature normalized. Sending re-arm SMS & full reset.");
        sendAlertToAll("[+] REARMEMENT SYSTEME : La temperature est repassee a la normale (" + String(currentTemperature, 1) + "C).");

        criticalAlertTriggered = false;
        tooColdAlertTriggered = false;
        tooHotAlertTriggered = false;
        isAlertModeActive = false;
        
        display.invertDisplay(false);
        display.clearDisplay();
        display.ssd1306_command(SSD1306_DISPLAYOFF);
        
        enterDeepSleep();
      }
    }
    return; 
  }

  static int lastButtonState = LOW; 
  static int buttonState = HIGH;
  static unsigned long lastDebounceTime = 0;
  const unsigned long debounceDelay = 40;

  static int clickCount = 0;
  static unsigned long firstClickTime = 0;
  const unsigned long doubleClickWindow = 400; 

  bool simpleClickDetected = false;
  bool doubleClickDetected = false;
  static unsigned long lastScreenRefreshTime = 0;

  if (millis() - lastScreenRefreshTime >= 1000) {
    lastScreenRefreshTime = millis();
    readProbe(); 
    updateDisplay();
  }

  int reading = digitalRead(BUTTON_PIN);
  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != buttonState) {
      buttonState = reading;
      if (buttonState == LOW) { 
        lastActionTime = millis(); 
        if (clickCount == 0) {
          firstClickTime = millis();
          clickCount = 1;
        } else if (clickCount == 1 && (millis() - firstClickTime) < doubleClickWindow) {
          doubleClickDetected = true;
          clickCount = 0;
        }
      }
    }
  }
  lastButtonState = reading;

  if (clickCount == 1 && (millis() - firstClickTime) >= doubleClickWindow) {
    simpleClickDetected = true;
    clickCount = 0;
  }

  if (simpleClickDetected) {
    currentMenuInt++;
    if (currentMenuInt > BATTERY) currentMenuInt = TEMPERATURE;
    isDiagRunning = false; 
    updateDisplay();
  }

  if (doubleClickDetected) {
    if (currentMenuInt == MIN_MAX) {
      minTemp = currentTemperature;
      maxTemp = currentTemperature;
      Serial.println("[MONITOR - NAV] Bounds historical data cleared.");
    } 
    else if (currentMenuInt == DIAGNOSTIC) {
      display.clearDisplay();
      display.setCursor(0, 20); display.setTextSize(1);
      display.println("Running analysis...");
      display.println("Booting 4G GSM...");
      display.display();

      turnOnModem();
      if (Modem.restart()) {
        isModemDiagOK = true;
        if (strlen(GSM_PIN) > 0 && Modem.getSimStatus() != 3) {
          Modem.simUnlock(GSM_PIN);
          delay(2000);
        }
        isSimDiagOK = (Modem.getSimStatus() == 1);
      } else {
        isModemDiagOK = false;
        isSimDiagOK = false;
      }
      turnOffModem(); 
      isDiagRunning = true; 
    } 
    else if (currentMenuInt == TEST_SMS) {
      display.clearDisplay();
      display.setCursor(0, 20); display.setTextSize(1);
      display.println("Sending test SMS...");
      display.println("Please wait...");
      display.display();
      
      bool testResult = sendAlertToAll("[TEST] Verified test alert message from ARN Monitor system.");
      
      display.clearDisplay();
      display.setCursor(0, 25);
      display.println(testResult ? "SMS Sent: SUCCESS!" : "SMS Sent: FAILED!");
      display.display();
      delay(2000);
    }
    else if (currentMenuInt == REBOOT) {
      display.clearDisplay();
      display.setTextSize(1);
      display.setCursor(0, 25);
      display.println("Rebooting system...");
      display.display();
      delay(1500);
      ESP.restart(); 
    }
    updateDisplay();
  }

  if (!isDiagRunning && (millis() - lastActionTime >= SCREEN_TIMEOUT)) {
    display.ssd1306_command(SSD1306_DISPLAYOFF); 
    enterDeepSleep();
  }
}

void enterDeepSleep() {
  turnOffModem(); 
  Wire.end();          

  // CORRECTIF 2 : Maintenir fermement la ligne BAT_EN à LOW via le loquet matériel RTC 
  // Cela empêche le modem de s'agiter électriquement et de polluer les broches voisines pendant le sommeil
  pinMode(BAT_EN, OUTPUT);
  digitalWrite(BAT_EN, LOW);
  gpio_hold_en((gpio_num_t)BAT_EN);
  gpio_deep_sleep_hold_en();

  // CORRECTIF 3 : Activer explicitement la résistance Pull-Up matérielle du domaine RTC sur le bouton.
  // Cela l'empêche de devenir "flottant" lorsque le processeur principal s'éteint.
  rtc_gpio_init((gpio_num_t)BUTTON_PIN);
  rtc_gpio_set_direction((gpio_num_t)BUTTON_PIN, RTC_GPIO_MODE_INPUT_ONLY);
  rtc_gpio_pullup_en((gpio_num_t)BUTTON_PIN);
  rtc_gpio_pulldown_dis((gpio_num_t)BUTTON_PIN);

  // Configuration des deux sources de réveil valides
  esp_sleep_enable_timer_wakeup(TIME_TO_SLEEP * 1000000ULL);
  esp_sleep_enable_ext0_wakeup((gpio_num_t)BUTTON_PIN, 0); // Réveil uniquement sur un vrai niveau BAS stabilisé
  
  Serial.println("[MONITOR - ECO] Halting processor core. System entering Deep Sleep.\n");
  Serial.flush();
  
  delay(100); // Petit délai de sécurité pour laisser les tensions transitoires se stabiliser
  esp_deep_sleep_start();
}

// - - - - - [ OLED RENDER ENGINE ] - - - - -
void updateDisplay() {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  
  if (isProbeFaulty) {
    display.setTextSize(2); display.setCursor(0, 10); display.println("!! ERROR !!");
    display.setTextSize(1); display.setCursor(0, 40); display.println("PROBE DISCONNECTED");
    display.println("Check PT100 wiring");
    display.display();
    return;
  }

  switch (currentMenuInt) {
    case TEMPERATURE:
      display.setTextSize(1); display.setCursor(0, 0); display.print("Menu: TEMPERATURE");
      display.setTextSize(2); display.setCursor(0, 22);
      display.print(currentTemperature, 1); display.write(247); display.print("C");
      display.setTextSize(1); display.setCursor(0, 53); display.print("Status: ");
      display.print(currentTemperature > CRITICAL_THRESHOLD ? "ALERT" : "Nominal");
      break;

    case MIN_MAX:
      display.setTextSize(1); display.setCursor(0, 0); display.println("Menu: MIN / MAX TEMP");
      display.setCursor(0, 18); display.print("Min: "); display.print(minTemp, 1); display.write(247); display.println("C");
      display.setCursor(0, 32); display.print("Max: "); display.print(maxTemp, 1); display.write(247); display.println("C");
      display.setCursor(0, 52); display.print("(Dbl-click to reset)");
      break;

    case THRESHOLDS: 
      display.setTextSize(1); display.setCursor(0, 0); display.println("Menu: SEUILS REGLES");
      display.setCursor(0, 18); display.print("Froid Max : "); display.print(TOO_COLD_THRESHOLD, 1); display.write(247); display.println("C");
      display.setCursor(0, 32); display.print("Alerte    : >"); display.print(CRITICAL_THRESHOLD, 1); display.write(247); display.println("C");
      display.setCursor(0, 46); display.print("Chaud Max : "); display.print(TOO_HOT_THRESHOLD, 1); display.write(247); display.println("C");
      break;

    case DIAGNOSTIC:
      display.setTextSize(1); display.setCursor(0, 0); display.println("Menu: SYSTEM DIAG");
      if (!isDiagRunning) {
        display.setCursor(0, 28); display.println("-> Double-click"); display.println("   to launch");
      } else { 
        display.setCursor(0, 18); display.print("PT100 Probe: OK"); 
        display.setCursor(0, 32); display.print("4G Modem   : "); display.println(isModemDiagOK ? "OK" : "ERR");
        display.setCursor(0, 46); display.print("SIM Card   : "); display.println(isSimDiagOK ? "READY" : "ERR/PIN");
      }
      break;

    case TEST_SMS:
      display.setTextSize(1); display.setCursor(0, 0); display.println("Menu: TEST NETWORK");
      display.setCursor(0, 28); display.println("-> Double-click");
      display.println("   to send test SMS");
      break;

    case REBOOT:
      display.setTextSize(1); display.setCursor(0, 0); display.println("Menu: REBOOT BOARD");
      display.setCursor(0, 28); display.println("-> Double-click");
      display.println("   to clear & reboot");
      break;

    case BATTERY: {
      display.setTextSize(1); display.setCursor(0, 0); display.println("Menu: BATTERY STATUS");
      
      int percentage = map(constrain(currentBatteryVoltage * 100, 320, 420), 320, 420, 0, 100);

      display.setCursor(0, 20); display.print("Voltage : "); display.print(currentBatteryVoltage, 2); display.println(" V");
      display.setCursor(0, 35); display.print("Capacity: "); display.print(percentage); display.println(" %");
      display.setCursor(0, 53); display.print("GSM line: STANDBY");
      break;
    }
  }
  display.display();
}