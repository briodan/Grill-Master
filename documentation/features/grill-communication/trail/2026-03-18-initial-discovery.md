# Initial Grill Discovery and Protocol Analysis

- Date: 2026-03-18
- Feature: grill-communication
- Related code: N/A (pre-implementation)

## Context

Performed initial network discovery of the LG1000BL at 192.168.1.100. The grill was connected to the local WiFi network and responsive on port 80.

## Discovery Results

1. **Port 80 open**: Serves a login page HTML (cosmetic only) and the Mongoose OS RPC interface
2. **RPC endpoints unauthenticated**: All 50+ RPC methods accessible without credentials
3. **`Sys.GetInfo` confirmed**: ESP32, Mongoose OS 2.17.0, firmware 0.2.3, device ID LBL-EXAMPLE
4. **`RPC.List` enumerated all methods**: Including `PB.GetState`, `PB.SendMCUCommand`, OTA, filesystem, and config methods
5. **`PB.GetState` returns hex payloads**: `sc_11` (FE0B status) and `sc_12` (FE0C temperature)
6. **`PB.GetFirmwareVersion`**: Reports 0.2.3

## Decision

Use the local HTTP RPC interface as the primary communication channel. This avoids:
- BLE range limitations
- Cloud dependency (Dansons WebSocket server)
- Authentication complexity (firmware 0.2.3 predates the auth requirement)

## Alternatives Considered

- **Option A: BLE via pytboss** - Would require a BLE-capable host device near the grill. More complex, range-limited.
- **Option B: Cloud WebSocket** - `wss://socket.dansonscorp.com/to/{id}` - Requires Dansons account login, cloud dependency, higher latency.
- **Option C: Local HTTP RPC** (chosen) - Direct, fast, no dependencies, no auth needed on this firmware.

## Consequences

- Positive: Simplest integration path, lowest latency, no cloud dependency, no BLE hardware needed
- Positive: Full access to all RPC methods including OTA, config, and filesystem
- Negative: If firmware is updated to 0.5.7+, authentication will be required (time-based key derivation)
- Negative: Grill must be on the same local network as the backend service
