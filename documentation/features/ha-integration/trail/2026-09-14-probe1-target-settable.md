# Probe 1 Target Is Settable Via the API; Probes 2-4 Are Not

- Date: 2026-09-14
- Feature: ha-integration
- Related code: `custom_components/grill_master/number.py`, `decoder.py`, `api.py`, `const.py`, `temp_unit.py`

## Context

Only a "Probe 1 Target" sensor was ever showing up in HA - no "Probe 2
Target" - and the question came up whether probe target temperatures can
be set via the API at all, or whether they're read-only.

## Investigation

Checked pytboss's `grills.json` (the source `decoder.py` was ported from)
for the `LBL` control board, which is what the `LG1000BL` model entry maps
to (this repo's "Control Board 8" is an informal name for the same board):

- `status_function`/`temperature_function` only ever compute a `p1Target`
  field. There is no `p2Target`/`p3Target`/`p4Target` byte anywhere in the
  FE0B or FE0C payload layout for this board - probes 2-4 report
  temperature only. This matches pytboss's own catalog-wide numbers: of
  137 grill models, only 42 report `p1Target` and 26 report `p2Target` at
  all.
- `control_board_commands` for `LBL` includes a slug
  `set-prove-1-temperature` (vendor's own typo for "probe") encoding
  `FE0502` + hundreds + tens + ones + `FF` - identical in shape to
  `set-temperature`'s `FE0501...`, just a different command byte. There is
  **no** `set-probe-2-temperature` (or 3/4) command declared for this
  board. pytboss falls back to a separate "virtual data" RPC store
  (`PB.GetVirtualData`/`PB.SetVirtualData`) for probes without a native
  command, but that's a distinct mechanism this integration doesn't
  implement.

So: Probe 1's target is both reportable and settable on this hardware.
Probes 2-4 are neither - there is nothing to add for them.

## Decision

- Added `encode_set_probe1_target()` to `decoder.py` (factored out of
  `encode_set_temperature()` via a shared `_encode_temperature_command()`
  helper, since the two commands are identical except for one byte) and
  `GrillMasterApi.set_probe_1_target()` in `api.py`.
- Added a `number` platform (`number.py`) exposing "Probe 1 Target" as a
  settable `NumberEntity`, mirroring `climate.py`'s pattern: detect HA's
  configured temperature unit and convert bounds/value to match, since
  the grill's own probe-target concept is Fahrenheit-only.
- Extracted the Fahrenheit <-> display-unit conversion logic that
  `climate.py` already had into a shared `temp_unit.py` module, used by
  both `climate.py` and `number.py`, to avoid a second copy of the same
  conversion helpers.
- `PROBE_TARGET_MIN_F`/`MAX_F`/`STEP_F` (32-210F, step 1) in `const.py` are
  a UI-only bound - the board doesn't enforce any range on this command,
  unlike the grill's own 180-600F/5F-increment setpoint.

## Alternatives Considered

- **Implement the "virtual data" fallback so probes 2+ could have a
  UI-only target** (as pytboss does for boards without a native command) -
  rejected. That's Traeger's own cloud-app convention (a target stored in
  virtual data is a note to whoever is watching, not something the board
  enforces), a materially different RPC surface
  (`PB.GetVirtualData`/`PB.SetVirtualData`) this integration has never
  implemented, and out of scope for what was asked (checking whether the
  *board* supports setting probe targets).
