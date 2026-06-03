# Faulty Ultralow-temperature Freezer Alarm - Schematics V2.0

## ⟪ DESCRIPTION ⟫

This repository contains all the hardware design files for the electronic board created as part of this project.

This project involves the design, schematic capture, and routing of a printed circuit board (PCB) meeting the specifications of the system requirements.
This major revision builds upon the core system (V1.4) by introducing local monitoring capabilities, ambient room temperature tracking, and a physical interface for on-site interaction.

## ⟪ TECHNICAL SPECIFICATIONS ⟫

▰ **CAD Software** ➢ KiCad 9.0.

▰ **Design Rules** ➢ Default track width: 20th (0.508 mm).

▰ **Layer Count** ➢ 1 layer (Bottom).

▰ **Core Components** ➢ LilyGo T-A7670E (ESP32-WROVER with integrated 4G LTE modem), Adafruit MAX31865 RTD amplifier, and PT100 temperature probe interface.

▰ **Added Peripherals (V2.0)** ➢ TMP102 ambient temperature sensor, local alert buzzer, and SSD1315 OLED display module equipped with 4 built-in navigation buttons.

## ⟪ WIRING SCHEMATIC ⟫

<img width="1090" height="707" alt="WiringSchemeV2 5" src="https://github.com/user-attachments/assets/33725fa1-a795-4531-9ca4-cc7ca3994376" />

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

