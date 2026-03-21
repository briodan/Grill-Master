# Home Assistant Integration 

- Date: 2026-03-18
- Feature: ha-integration
- Related code: `custom_components/grill_master/`

## Context

The original GrillMaster architecture 
Home Assistant custom integration (Python) — local monitoring/control + optional cloud sync

The HA integration talks directly to the grill over local HTTP and optionally pushes data to a PHP cloud endpoint.

## Decision

Build a Home Assistant custom integration as the primary interface to the grill, rather than a standalone C# backend.

The integration:
- Uses Python (required by HA platform)
- Ports payload decoding from the `pytboss` library (JavaScript → Python)
- Communicates via HTTP JSON-RPC (not BLE like the existing `ha-pitboss` integration)
- Includes configurable cloud sync to POST temperature data to a PHP endpoint

## Alternatives Considered

- **Option A: Use existing ha-pitboss integration** — Only supports BLE and WebSocket (cloud). The LG1000BL's HTTP JSON-RPC interface is not supported. Would require a fork.
- **Option B: Custom HA integration with local HTTP** (chosen) — Direct, simple, leverages HA ecosystem, no cloud dependency for local monitoring.

## Consequences

- Positive: Immediate value via HA ecosystem (automations, notifications, Lovelace dashboards)
- Positive: No custom backend needed for local monitoring
- Positive: HA handles unit conversion, device registry, entity management
- Positive: Cloud sync is optional and non-blocking
- Negative: Monitoring requires a running Home Assistant instance
- Negative: HA custom components must be Python 
- Negative: Only supports firmware 0.2.3 (unauthenticated); newer firmware needs additional work
