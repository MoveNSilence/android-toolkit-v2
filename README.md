# android-toolkit-v2

A toolkit for interacting with Android devices.

## ADB Connector

The `src/adb_connector.py` script allows you to connect to an Android device over TCP/IP and list its partitions.

### Prerequisites

-   Python 3
-   ADB (Android Debug Bridge) installed and in your system PATH.
-   Wireless debugging enabled on your Android device (or TCP/IP enabled via USB).

### Usage

Run the script from the root of the repository:

```bash
python3 src/adb_connector.py <DEVICE_IP>:<PORT>
```

Example:

```bash
python3 src/adb_connector.py 192.168.1.15:5555
```
