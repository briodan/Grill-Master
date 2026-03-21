# GrillMaster

## Project Overview

Cross-platform app for monitoring and controlling an LG1000BL pellet grill over the local network. Real-time temperature monitoring with intelligent alarms.

## Architecture (3-Part)

- Home Assistant custom integration (Python) — `custom_components/grill_master/`
  - Local grill communication via HTTP JSON-RPC
  - Temperature sensors, binary sensors, climate control, light switch
  - Optional cloud sync to  backend

## Target Device

- LG1000BL (Black Label), ESP32/Mongoose OS
- Local RPC at `http://<grill-ip>/rpc/` (no auth on firmware 0.2.3)
- Key endpoints: `PB.GetState` (temps), `PB.SendMCUCommand` (control)
- Data format: hex-encoded MCU payloads (FE0B=status, FE0C=temperature)


## Key Directories

- `custom_components/grill_master/` - Home Assistant integration (Part 1)
- `documentation/` - Feature docs, baselines, and decision trails
- `documentation/planning/` - Project plan and phase planning
- `documentation/features/` - Per-feature documentation

## Documentation Convention

Follow `documentation/README.md` for documentation structure. Each feature has:
- `<feature>.md` - Current behavior and flow
- `baseline.md` - Expected behavior invariants
- `trail/` - Decision history entries

## Critical Feature

Temperature alarms are the #1 priority. Joe must be notified when grill temperature drifts more than the configured threshold (default 5F) from the set point.
