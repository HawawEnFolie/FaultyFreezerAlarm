Faulty Ultralow-temperature Freezer Alarm - Schematics
⟪ DESCRIPTION ⟫
This directory contains the electronic schematics, PCB layouts, and hardware design files for the FaultyFreezerAlarm project. The hardware has been developed iteratively to meet the specific telemetry and monitoring requirements of the UPPA microbiology laboratories.

⟪ HARDWARE VERSIONS ⟫
▰ Version 1.4 (Core System) ⪢ This hardware revision focuses strictly on the essential components required for ultra-low temperature monitoring and remote LTE alerting.

Core Components: LilyGo T-A7670E (ESP32-WROVER with integrated 4G LTE modem), Adafruit MAX31865 RTD amplifier, and the PT100 temperature probe interface.

▰ Version 2.0 (Full System) ⪢ This major revision expands upon V1.4 by introducing local monitoring capabilities, ambient room tracking, and a physical user interface for on-site interaction.

Core Components: All essential components from V1.4.

Added Peripherals: A TMP102 ambient temperature sensor, a local alert buzzer, and an SSD1315 OLED display module equipped with 4 built-in navigation buttons.

⟪ DESIGN TOOLS ⟫
▰ Schematic & PCB Routing ⪢ KiCad 9.0.
