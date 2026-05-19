# FaultyFreezerAlarm
📝 Project Description
This repository contains the source code and documentation for a critical telemetry embedded system. Developed during the first year of the BTS CIEL ER program to meet the needs of the UPPA (University of Pau and the Adour Region) research laboratories, this system monitors the temperature of ultra-low temperature freezers in real time.

If the temperature crosses the critical threshold of -80°C, the system triggers an immediate SMS alert via a 4G LTE cellular network to the laboratory manager, allowing for rapid intervention to save samples.

✨ Key Features
High-Precision Acquisition: Temperature reading every 10 seconds via an industrial PT100 probe and a MAX31865 amplifier (SPI communication).

Cellular Connectivity (LTE): Automated SMS alerts sent over the mobile network using AT commands on a SIMCom A7670E module.

Anti-Spam Logic (State Machine): The system incorporates a software lock to send only one SMS when the threshold is crossed, automatically resetting once the temperature stabilizes below -80°C.

Local Monitoring: Real-time display of readings and network status on the serial monitor (9600 baud).

🛠️ Hardware Requirements
Microcontroller & Modem: LilyGo T-A7670E development board (Based on an ESP32-WROVER with an integrated 4G LTE modem).

RTD Amplifier: Adafruit MAX31865 module (Breakout board).

Sensor: PT100 temperature probe (configurable for 2, 3, or 4 wires).

Power & Connectivity: Active SIM card (with an SMS plan) and suitable power supply for the LilyGo board.

💻 Software Environment
IDE: Visual Studio Code with the PlatformIO extension.

Framework: Arduino (C++).

Dependencies & Libraries:

Adafruit MAX31865 library (Handling of the sensor's analog-to-digital conversion).

TinyGSM (Seamless handling of AT commands and communication with the SIMCom modem).


