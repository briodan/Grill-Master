# GrillMaster Project Plan

- Date: 2026-03-18

## Vision

A cross-platform app (web, mobile, desktop) that gives full local control and monitoring of an LG1000BL pellet grill over the local network, with real-time temperature tracking and intelligent alarms.

## Target Device

- **Model**: LG1000BL (Black Label)
- **Controller**: ESP32 running Mongoose OS 2.17.0
- **Firmware**: v0.2.3
- **Device ID**: LBL-EXAMPLE
- **Local IP**: 192.168.1.100
- **Communication**: HTTP JSON-RPC at `http://<grill-ip>/rpc/`
- **Authentication**: None required on local network (firmware 0.2.3)
- **Data Format**: Hex-encoded MCU payloads (FE0B = status, FE0C = temperature)
- **Meat Probes**: 2
- **Temperature Range**: 180-600 F

## Available Grill RPC Endpoints

Discovered via local network scan on 2026-03-18:

### Primary (App Use)

| Endpoint                    | Purpose                                                           |
| --------------------------- | ----------------------------------------------------------------- |
| `PB.GetState`               | Returns hex-encoded status (FE0B) and temperature (FE0C) payloads |
| `PB.SendMCUCommand`         | Send hex commands: set temp, power, light, primer, units          |
| `PB.GetFirmwareVersion`     | Returns `{"firmwareVersion": "0.2.3"}`                            |
| `PB.GetVirtualData`         | Virtual sensor data                                               |
| `PB.SetMCU_UpdateFrequency` | Control how often MCU sends status updates                        |
| `PB.SetWiFiUpdateFrequency` | Control WiFi update interval                                      |

### System / Diagnostics

| Endpoint      | Purpose                               |
| ------------- | ------------------------------------- |
| `Sys.GetInfo` | Device ID, firmware, RAM, WiFi status |
| `Sys.Reboot`  | Reboot the controller                 |
| `RPC.List`    | List all available RPC methods        |
| `RPC.Ping`    | Connectivity check                    |
| `Config.Get`  | Read device configuration             |

### Known MCU Command Hex Codes

| Command               | Hex                                           |
| --------------------- | --------------------------------------------- |
| Turn Grill Off        | `FE0102FF`                                    |
| Turn Light On         | `FE0201FF`                                    |
| Turn Light Off        | `FE0200FF`                                    |
| Turn Primer Motor On  | `FE0801FF`                                    |
| Turn Primer Motor Off | `FE0800FF`                                    |
| Set Celsius           | `FE0902FF`                                    |
| Set Fahrenheit        | `FE0901FF`                                    |
| Set Grill Temperature | Dynamic (see grill-communication feature doc) |

### Sample State Response

```json
{
  "sc_12": "FE0C00000000000009060009060009060000000000000001FF",
  "sc_11": "FE0B00000000000009060000000000000000000002020001000000000000000000000100000000FF"
}
```

- `sc_11` = Status payload (FE0B prefix)
- `sc_12` = Temperature payload (FE0C prefix)
