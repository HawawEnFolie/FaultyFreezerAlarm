# FFA Terminal - Asset Environment Monitoring Interface

## ⟪ DESCRIPTION ⟫

This directory contains the Python-based desktop application used as the central control and telemetry hub for the FaultyFreezerAlarm system. Designed to run locally on a computer connected to the LilyGo T-A7670E (ESP32), it provides a complete graphical user interface to monitor the ultra-low temperature freezers of the UPPA microbiology laboratories. It allows for real-time visualization of sensor data, comprehensive hardware diagnostics, and remote configuration of critical system thresholds without needing to recompile the C++ firmware.

## ⟪ FEATURES ⟫

**▰ Smart Serial Connection ⪢** Includes an auto-detect feature to automatically find the ESP32 on active COM ports and an auto-recovery loop to re-establish the link in case of a hardware drop.

**▰ Core Configuration Management ⪢** Read, edit, and push system thresholds (e.g., `PT100_CRITICAL`, `TMP102_CRITICAL`) directly to the ESP32's non-volatile memory.

**▰ Glossary & Dispatch Hub ⪢** A built-in address book to manage the up to 10 phone numbers of the researchers receiving SMS alerts. Allows syncing numbers to the hardware while keeping researcher names in local volatile RAM.

**▰ Live Telemetry & Graphing ⪢** Real-time plotting of the PT100 and TMP102 temperatures against time. Includes the ability to log this data and export it as `.txt` or `.csv` files for scientific tracking.

**▰ Advanced Modem Diagnostics ⪢** Visual status indicators for the SIMCom LTE modem's connection quality, displaying exact values and quality ratings for RSSI, RSRP, RSRQ, and SINR.

**▰ Remote Hardware Testing ⪢** Dedicated diagnostic routines to verify the integrity of the PT100 probe, the ambient sensor, the modem, and the SIM card. Includes a feature to force a test SMS dispatch and perform a soft reboot of the ESP32.

**▰ Integrated Easter Egg ⪢** Contains a fully playable, top-secret Tower Defense mini-game ("Orchidéfense") hidden within the credits tab, featuring lab-themed enemies and hardware-based defensive towers.

## ⟪ SOFTWARE REQUIREMENTS ⟫

**▰ Language ⪢** Python 3.x

**▰ OS Compatibility ⪢** Windows / Linux / macOS (Tkinter must be supported by the host OS).

## [ Dependencies & Libraries ]

**▰** `tkinter` (Standard GUI library for the interface panels and the mini-game canvas).
**▰** `pyserial` (Handling of the serial communication and COM port polling).
**▰** `matplotlib` (Rendering of the real-time temperature graph and data plotting).

## ⟪ LICENSE ⟫

The source code of this interface is licensed under the **GNU General Public License v3.0 (GPLv3)**. 
See the main repository LICENSE file for more details.
