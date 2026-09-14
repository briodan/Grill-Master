# Grill Communication

- Tech: HttpClient

## Overview

The grill communication layer is the bridge between the GrillMaster backend and the LG1000BL hardware. It handles all direct communication with the grill's Mongoose OS RPC interface over the local network.

## Device Details

- **Controller**: ESP32 running Mongoose OS 2.17.0
- **Firmware**: v0.2.3 (built 2020-10-01)
- **Device ID**: LBL-EXAMPLE
- **MAC**: 94:3C:C6:XX:XX:XX
- **Protocol**: HTTP JSON-RPC
- **Base URL**: `http://<grill-ip>/rpc/<method>`
- **Authentication**: None required (firmware 0.2.3 predates auth requirement at 0.5.7+)
- **Meat Probes**: 2
- **Temperature Range**: 180-600 F

## RPC Communication Pattern

All grill communication uses HTTP GET or POST to `http://<ip>/rpc/<MethodName>`.

Responses are JSON. State data is returned as hex-encoded MCU payloads that require decoding.

### Polling Flow

```
Backend Polling Service (IHostedService)
    |
    |-- Every N seconds (configurable, default 3s) -->
    |
    |   GET http://<ip>/rpc/PB.GetState
    |   Response: { "sc_11": "FE0B...", "sc_12": "FE0C..." }
    |
    |-- Decode hex payloads -->
    |
    |   sc_11 (FE0B) -> GrillStatus object
    |   sc_12 (FE0C) -> TemperatureReading object
    |
    |-- Push to SignalR hub + store in SQLite -->
    |
    |-- Evaluate alarm conditions -->
```

### Sending Commands

Commands are sent via `PB.SendMCUCommand` with hex-encoded payloads.

```
POST http://<ip>/rpc/PB.SendMCUCommand
Body: { "id": <0-2047>, "params": { "command": "<hex>" } }
```

## MCU Payload Decoding

### Status Payload (FE0B)

`sc_11` contains the grill status. Prefix: `FE0B`.

Fields to decode (byte offsets from start of payload, after FE0B prefix):
- Grill power state (on/off)
- Current set temperature
- Fire control state
- Error codes
- Unit setting (F/C)

### Temperature Payload (FE0C)

`sc_12` contains temperature readings. Prefix: `FE0C`.

Fields to decode:
- Grill temperature (current)
- Meat probe 1 temperature
- Meat probe 2 temperature
- Set point temperature

**Reference implementation**: The `pytboss` Python library (github.com/dknowles2/pytboss) contains the complete payload decoder.  should port the decoding logic from `pytboss/codec.py` and `pytboss/grills.py` .

### Known Command Hex Codes

| Command | Hex | Notes |
|---|---|---|
| Turn Grill Off | `FE0102FF` | |
| Turn Light On | `FE0201FF` | |
| Turn Light Off | `FE0200FF` | |
| Turn Primer Motor On | `FE0801FF` | |
| Turn Primer Motor Off | `FE0800FF` | |
| Set Celsius | `FE0902FF` | |
| Set Fahrenheit | `FE0901FF` | |
| Set Grill Temperature | Dynamic | `FE0501`+hex(hundreds)+hex(tens)+hex(ones)+`FF` |
| Set Probe 1 Target Temperature | Dynamic | `FE0502`+hex(hundreds)+hex(tens)+hex(ones)+`FF`. No equivalent for probes 2+ |

## C# Implementation Notes

### GrillRpcClient

```
Services/
  GrillRpcClient.cs       - HttpClient wrapper for all RPC calls
  McuPayloadDecoder.cs     - Hex payload -> C# models
  GrillPollingService.cs   - IHostedService that polls on interval
  GrillCommandService.cs   - Send commands (set temp, power, light)
Models/
  GrillStatus.cs           - Decoded status payload
  TemperatureReading.cs    - Decoded temperature payload
  GrillCommand.cs          - Command definitions
  GrillInfo.cs             - Device info from Sys.GetInfo
```

### Error Handling

- If the grill becomes unreachable (network timeout), the polling service should:
  1. Mark the grill as "disconnected" in state
  2. Push a disconnection event via SignalR
  3. Continue polling at a reduced rate (every 10s) until reconnected
  4. Trigger a "grill disconnected" alarm if configured
- HTTP timeouts should be set to 5 seconds max to avoid blocking

### Configuration

```json
{
  "Grill": {
    "IpAddress": "192.168.1.100",
    "PollIntervalSeconds": 3,
    "TimeoutSeconds": 5,
    "DisconnectedPollIntervalSeconds": 10
  }
}
```

## Integration Points

- **Temperature Monitoring feature**: Consumes decoded temperature readings
- **Alarm Engine**: Evaluates decoded readings against thresholds
