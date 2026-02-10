# Android Toolkit v2 - God Tool (Samsung/Motorola)

A specialized toolkit for Android device security analysis and modification, targeting Samsung and Motorola devices.

## Features

- **IMEI Generation:** Generate valid 15-digit IMEIs using the Luhn algorithm.
  - Default Samsung TAC: `358270`.
  - Supports custom TAC input.
- **EFS/NVRAM Operations:**
  - **Backup:** Securely dump `modemst1`, `modemst2`, and `fsg` partitions with MD5 checksum verification.
  - **Wipe:** Safely wipe EFS partitions (requires a verified backup).
  - **Inject:** Modify partition images with new IMEI data (requires valid offset).
- **Diagnostics:** Enable Diag Mode (`sys.usb.config diag,adb`).
- **ADB Connectivity:** Connect to devices over TCP/IP.
- **InternalBlue Integration:**
  - **Sync-Patch:** Synchronized IMEI injection and Bluetooth RAM patching with LMP monitoring for radio stability.

## Prerequisites

- Python 3
- ADB (Android Debug Bridge) installed and in your system PATH (`android-tools-adb`).
- Rooted Android device (Samsung or Motorola).
- Wireless debugging enabled or TCP/IP enabled via USB (`adb tcpip 5555`).

## Installation

Clone the repository:
```bash
git clone https://github.com/yourusername/android-toolkit-v2.git
cd android-toolkit-v2
```

## Usage

Run the tool using the wrapper script:

```bash
python3 src/god_tool.py <COMMAND> [OPTIONS]
```

### Commands

#### 1. Connect to Device
Test connection and list partitions.
```bash
python3 src/god_tool.py connect --ip 192.168.1.15:5555
```

#### 2. Generate IMEI
Generate a valid IMEI.
```bash
# Default Samsung TAC (358270)
python3 src/god_tool.py generate-imei

# Custom TAC
python3 src/god_tool.py generate-imei --tac 351234
```

#### 3. Enable Diag Mode
Enable diagnostic mode on the device.
```bash
python3 src/god_tool.py enable-diag --ip 192.168.1.15:5555
```

#### 4. Backup EFS
Backup security partitions to a local directory (default: `backups/`). verifies integrity via MD5.
```bash
python3 src/god_tool.py backup --ip 192.168.1.15:5555 --dir my_backups
```

#### 5. Wipe EFS (Dangerous)
Wipe security partitions. **Requires a valid backup in the specified directory.**
```bash
python3 src/god_tool.py wipe --ip 192.168.1.15:5555 --dir my_backups
```

#### 6. Inject IMEI (Advanced)
Inject a new IMEI into a partition image and flash it back to the device.
**Requires a valid backup file.**

```bash
python3 src/god_tool.py inject --target backups/modemst1.img --offset 0x1234 --imei 358270000000007 --ip 192.168.1.15:5555
```

#### 7. Sync Patch (InternalBlue Integration)
Inject IMEI into EFS partition and simultaneously patch Bluetooth RAM.
**Requires InternalBlue dependencies.**

```bash
python3 src/god_tool.py sync-patch --target backups/modemst1.img --offset 0x1234 --imei 358270000000007 --bt-addr 0x200000 --ip 192.168.1.15:5555
```

## Safety Mechanisms

- **LMP Monitoring:** Monitors Bluetooth Link Management Protocol packets during operations to ensure radio stability.
- **MD5 Verification:** All backups are verified against the on-device file hash before being considered successful.
- **Backup Check:** The wipe operation explicitly checks for the existence of backup files before proceeding.
- **Copy-on-Write:** The inject command creates a copy of the target backup before modifying it, preserving the original data.
- **Error Handling:** All ADB commands are wrapped with error checking.

## Disclaimer

This tool is for educational and research purposes only. Modifying device identifiers (IMEI) may be illegal in some jurisdictions. Use responsibly.
