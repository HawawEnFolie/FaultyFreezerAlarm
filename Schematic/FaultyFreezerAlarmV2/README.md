# Faulty Ultralow-temperature Freezer Alarm - Schematics V2.5

## ⟪ DESCRIPTION ⟫

This repository contains the hardware design files (schematics and PCB routing) for version 2.5 of the **FaultyFreezerAlarm** project. The hardware has been iteratively developed to meet the specific telemetry and monitoring requirements of the -80°C freezers at the UPPA microbiology laboratories. 

This major revision builds upon the core system (V1.4) by introducing local monitoring capabilities, ambient room temperature tracking, a physical interface for on-site interaction, and a power outage detection circuit.

## ⟪ TECHNICAL SPECIFICATIONS ⟫

▰ **CAD Software** ➢ KiCad 9.0.

▰ **Design Rules** ➢ Default track width: 20th (0.508 mm).

▰ **Layer Count** ➢ 1 layer (Bottom).

▰ **Core Components** ➢ LilyGo T-A7670E (ESP32-WROVER with integrated 4G LTE modem), Adafruit MAX31865 RTD amplifier, and PT100 temperature probe interface.

▰ **Added Peripherals (V2.5)** ➢ TMP102 ambient temperature sensor, local alert buzzer, SSD1315 OLED display module equipped with 4 built-in navigation buttons, and a voltage divider (R1 10kΩ / R2 20kΩ) connected to the USB VBUS pin for power loss detection.

## ⟪ WIRING SCHEMATIC ⟫

<img width="1090" height="707" alt="WiringSchemeV2 5" src="https://github.com/user-attachments/assets/a503183a-ab60-4b19-8bc6-0a146e51e3ff" />

## ⟪ PROJECT STRUCTURE ⟫

▰ **`*.kicad_pro`** ➢ Main KiCad project file.

▰ **`*.kicad_sch`** ➢ Electrical schematic file.

▰ **`*.kicad_pcb`** ➢ Printed circuit board routing file.

## ⟪ HOW TO OPEN THE PROJECT ⟫

▰ **Step 1** ➢ Ensure you have **KiCad (version 9.0 or higher)** installed.

▰ **Step 2** ➢ Clone this repository or download the files.

▰ **Step 3** ➢ Launch KiCad and open the `.kicad_pro` file located in the root directory.

## ⟪ AUTHOR ⟫

**Robin Paniagua Desclaux**
*Student in BTS CIEL ER (1st year)*
