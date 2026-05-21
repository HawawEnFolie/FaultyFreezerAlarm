#include <Arduino.h>
#include <Wire.h> 
#include <SPI.h>  
#include <Adafruit_MAX31865.h>

// - - - - - [ CONFIGURATION BUFFER & TINYGSM ] - - - - -
#define TINY_GSM_RX_BUFFER 1024 
#define TINY_GSM_MODEM_SIM7600 
#include <TinyGsmClient.h>

// - - - - - [ CONFIGURATION MODEM ] - - - - -
#define MODEM_TX     26
#define MODEM_RX     27
#define MODEM_PWRKEY 4
#define MODEM_RST    5
#define MODEM_DTR    25  
#define BAT_EN       12  
#define GSM_PIN      "4545"

HardwareSerial SerialAT(1);
TinyGsm Modem(SerialAT);

// - - - - - [ CONFIGURATION PT100 ] - - - - -
#define MAX_CS       15
Adafruit_MAX31865 Thermo = Adafruit_MAX31865(MAX_CS);
#define RREF         430.0 
#define RNOMINAL     100.0 

// - - - - - [ VARIABLES ] - - - - -
const char* NUMEROS_ALERTE[] = {
  "+33000000000", // Personne n°1 > Xxxxx XXXXXX
  "+33000000000", // Personne n°2 > Xxxxx XXXXXX
  "+33000000000", // Personne n°3 > Xxxxx XXXXXX
  "+33000000000", // Personne n°4 > Xxxxx XXXXXX
  "+33000000000"  // Personne n°5 > Xxxxx XXXXXX
};
String CONGELATEUR_CIBLE = "congelateur ARN dans chambre froide";
const int NOMBRE_NUMEROS = sizeof(NUMEROS_ALERTE) / sizeof(NUMEROS_ALERTE[0]);
const unsigned long INTERVALLE_LECTURE = 10000;
unsigned long DernierReleve = 0;

// - - - - - [ SEUILS DE DÉTECTION ] - - - - -
const float SEUIL_CRITIQUE   = -65.0;
const float SEUIL_TROP_FROID = -100.0;
const float SEUIL_TROP_CHAUD = 65.0;

// - - - - - [ BOOLÉENS ANTI-SPAM ] - - - - -
bool AlerteSeuilCritique = false;
bool AlerteTropFroid     = false;
bool AlerteTropChaud     = false;

// - - - - - [ SÉQUENCE D'ALLUMAGE ] - - - - -
void AllumerModem() {
  pinMode(BAT_EN, OUTPUT);
  digitalWrite(BAT_EN, HIGH);
  delay(1000); 

  pinMode(MODEM_DTR, OUTPUT);
  digitalWrite(MODEM_DTR, LOW); 

  pinMode(MODEM_RST, OUTPUT);
  digitalWrite(MODEM_RST, HIGH); 
  delay(200);

  // Impulsion d'allumage Active LOW (Méthode B validée)
  pinMode(MODEM_PWRKEY, OUTPUT);
  digitalWrite(MODEM_PWRKEY, HIGH);
  delay(100);
  digitalWrite(MODEM_PWRKEY, LOW);  
  delay(1500);                     
  digitalWrite(MODEM_PWRKEY, HIGH); 

  delay(6000); // Temps de démarrage du modem
}

// - - - - - [ LOGIQUE DES NUMÉROS ] - - - - -
bool EnvoyerAlerteATous(String message) {
  int NombreSucces = 0;

  for (int i = 0; i < NOMBRE_NUMEROS; i++) {
    if (!Modem.isNetworkConnected()) {
      Modem.waitForNetwork(10000L); 
    }

    if (Modem.sendSMS(NUMEROS_ALERTE[i], message)) {
      NombreSucces++;
    }
    delay(1000);
  }
  return NombreSucces > 0;
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n[ INFO ] Initialisation du programme...");

// - - - - - [ INITIALISATION PT100 ] - - - - -
  Thermo.begin(MAX31865_4WIRE); 
  if (Thermo.readFault()) {
    Serial.println("[ ! ERREUR ! ] Problème initial avec la sonde PT100.");
    Thermo.clearFault();
  }

// - - - - - [ SYNCHRONISATION MODEM SUR RÉSEAU 4G ] - - - - -
  AllumerModem();
  SerialAT.begin(115200, SERIAL_8N1, MODEM_RX, MODEM_TX);
  delay(3000);

  if (!Modem.restart()) {
    Serial.println("[ ERREUR ] Pas de réponse du modem.");
  } else {
    if (strlen(GSM_PIN) > 0 && Modem.getSimStatus() != 3) {
      Modem.simUnlock(GSM_PIN);
      delay(3000); 
    }

    if (Modem.waitForNetwork(60000L, true)) {
      Serial.println("[ INFO ] Modem connecté au réseau cellulaire 4G.");
    } else {
      Serial.println("[ ! ERREUR ! ] Impossible de joindre le réseau mobile 4G.");
    }
  }
  Serial.println("[ INFO ] Début de la surveillance.");
}

void loop() {
  if (millis() - DernierReleve >= INTERVALLE_LECTURE) {
    DernierReleve = millis();

    // Lecture et sécurité de la sonde
    uint16_t rtd = Thermo.readRTD();
    float Temperature = Thermo.temperature(RNOMINAL, RREF);

    if (Thermo.readFault()) {
      Serial.println("[ ! ERREUR ! ] Défaut ou coupure de la sonde PT100 ! Lecture annulée.");
      Thermo.clearFault();
      return;
    }

    // Affichage dans le moniteur de l'ordinateur
    Serial.print("[ INFO ] Température relevée : ");
    Serial.print(Temperature);
    Serial.println(" °C.");

// - - - - - [ ALERTE | FROID EXTRÊME ] - - - - -
    if (Temperature < SEUIL_TROP_FROID) {
      if (!AlerteTropFroid) {
        String msg = "[!] ALERTE POUR '" + CONGELATEUR_CIBLE + "' : Température anormalement basse à " + String(Temperature, 2) + " C.";
        if (EnvoyerAlerteATous(msg)) AlerteTropFroid = true;
      }
// - - - - - [ RÉARMEMENT POUR FROID EXTRÊME ] - - - - -
    } else {
      if (AlerteTropFroid) {
        AlerteTropFroid = false; // Réarmement
      }
    }

// - - - - - [ ALERTE | CHAUD EXTRÊME ] - - - - -
    if (Temperature > SEUIL_TROP_CHAUD) {
      if (!AlerteTropChaud) {
        String msg = "[!] ALERTE POUR '" + CONGELATEUR_CIBLE + "' : Température anormalement chaude à " + String(Temperature, 2) + " C.";
        if (EnvoyerAlerteATous(msg)) AlerteTropChaud = true;
      }
// - - - - - [ RÉARMEMENT POUR CHAUD EXTRÊME ] - - - - -
    } else {
      if (AlerteTropChaud) {
        AlerteTropChaud = false; // Réarmement
      }
    }

// - - - - - [ ALERTE | DÉPASSEMENT TEMPÉRATURE CRITIQUE ] - - - - -
    if (Temperature > SEUIL_CRITIQUE && Temperature <= SEUIL_TROP_CHAUD) {
      if (!AlerteSeuilCritique) {
        String msg = "[!] ALERTE POUR '" + CONGELATEUR_CIBLE + "' : Dépassement du seuil des -65°C ! température actuelle : " + String(Temperature, 2) + " C.";
        if (EnvoyerAlerteATous(msg)) AlerteSeuilCritique = true; 
      }
// - - - - - [ RÉARMEMENT POUR DÉPASSEMENT TEMPÉRATURE CRITIQUE ] - - - - -
    } else {
      if (Temperature <= SEUIL_CRITIQUE && AlerteSeuilCritique) {
        AlerteSeuilCritique = false;
      }
    }
  }
}