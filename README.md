# Faulty Ultralow-temperature Freezer Alarm

## ⟪ DESCRIPTION ⟫

This repository contains the source code and documentation for a critical telemetry embedded system. Developed during the first year of the BTS CIEL ER program to meet the needs of the UPPA (University de Pau et des Pays de l'Adour) microbiology laboratories, this system monitors the temperature of ultra-low temperature freezers in real time. If the temperature crosses a critical threshold, here -65°C, the system triggers an immediate SMS alert via a 4G LTE cellular network to designated rsearchers so as to reduce as much as possible the time where samples are not correctly frozen.

## ⟪ FEATURES ⟫

**▰ High-Precision Acquisition ⪢** Temperature reading every 10 minutes via an industrial PT100 probe and a MAX31865 amplifier (SPI communication).

**▰ Cellular Connectivity ⪢** Automated SMS alerts sent over the mobile network using AT commands on a SIMCom A7670E module.

**▰ Anti-Spam Logic ⪢** The system includes a software lock to send only one SMS when the threshold is crossed, automatically resetting once the temperature stabilizes below a set level, so as not a flood the target phones with multiple SMS.

**▰ Local Monitoring ⪢** Real-time display of readings and network status on the serial monitor with integrated DEBUG mode as well as screen to show live info about the PT100.

**▰ Ambient Temperature Tracking ⪢** Continuous measurement of the ambient room temperature utilizing a TMP102 sensor.

**▰ Local Alerts & Interface ⪢** An integrated buzzer for immediate audible alarms and an SSD1315 OLED display equipped with 4 integrated buttons for local navigation and control.

## ⟪ HARDWARE REQUIREMENTS ⟫

**▰ Microcontroller & Modem ⪢** LilyGo T-A7670E development board (Based on an ESP32-WROVER with an integrated 4G LTE modem).

**▰ RTD Amplifier ⪢** Adafruit MAX31865 module.

**▰ Sensor ⪢** PT100 temperature probe with 4 wires (can be configured for 2 and 3 wires as well).

**▰ Additional Peripherals ⪢** TMP102 ambient temperature sensor, alert buzzer, and an SSD1315 OLED display module with 4 built-in buttons.

**▰ Power & Connectivity ⪢** Active SIM card (with SMS plan) and suitable power supply for the LilyGo board.

## ⟪ SOFTWARE REQUIREMENTS ⟫

**▰ IDE ⪢** Visual Studio Code with the PlatformIO extension.

**▰ Framework ⪢** Arduino (C++).

## [ Dependencies & Libraries ]

**▰** Adafruit MAX31865 library (Handling of the sensor's analog-to-digital conversion).

**▰** TinyGSM (Seamless handling of AT commands and communication with the SIMCom modem).

## ⟪ LICENSE ⟫
The source code of this project is licensed under **GPLv3**.
The hardware design files (Schematics, PCB, 3D models) are licensed under **CERN-OHL-S v2**.
See the LICENSE and cern_ohl_s_v2.txt files for more details.









