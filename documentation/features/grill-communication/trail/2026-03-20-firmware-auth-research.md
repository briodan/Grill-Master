# Firmware Authentication Research

- Date: 2026-03-20
- Feature: grill-communication
- Related code: `custom_components/grill_master/api.py`, `custom_components/grill_master/decoder.py`

## Context

Researched how newer firmware versions handle authentication, based on analysis of the pytboss library (`codec.py`, `api.py`). Our integration currently only supports firmware 0.2.3, which has no authentication. This documents what would be needed to support newer firmware.

## Findings

### Firmware 0.2.3 (Current - Unauthenticated)

- All RPC endpoints are open on the local network with no auth
- `PB.GetTime` endpoint does **not exist** (returns 404)
- No password can be set on the device
- This is the firmware version on the LG1000BL Black Label series as of 2026

### Newer Firmware (Authenticated)

Newer firmware versions (version threshold undocumented — pytboss does not specify a cutoff) add:

1. **`PB.GetTime` endpoint** — Returns device uptime in seconds: `{"time": 12345.67}`
2. **`PB.SetDevicePassword`** — Allows setting a grill password
3. **Password-protected commands** — When a password is set, most commands require a `psw` parameter

### Time-Based Key Derivation (from pytboss `codec.py`)

The auth mechanism uses a symmetric XOR cipher with a time-derived key:

#### Fixed Seed Key
```python
KEY = [0x8F, 0x80, 0x19, 0xCF, 0x77, 0x6C, 0xFE, 0xB7]  # 8 bytes
```

#### `timed_key(uptime)` Algorithm
1. Takes the device uptime (float, from `PB.GetTime`)
2. Applies a 10-second buffer/rounding to the uptime value
3. Iteratively mutates the fixed KEY array using XOR with a counter variable
4. Returns a derived key that changes over time

#### `encode(data, key)` Algorithm
1. Generate 16 bytes of random padding
2. Prepend padding + `0xFF` delimiter to the plaintext data
3. XOR-encrypt the entire payload using the timed key
4. Key state mutates on each byte (depends on iteration index and ciphertext)
5. Return encrypted bytes

#### `decode(data, key)` Algorithm
1. XOR-decrypt using the same mutating key process
2. Find the first `0xFF` byte — everything before it is padding, everything after is plaintext
3. Return the plaintext

### How Authentication is Applied (from pytboss `api.py`)

```python
async def _authenticate(self, params: dict) -> dict:
    if self._password:
        params["psw"] = encode(
            self._password, key=timed_key(await self.get_uptime())
        ).hex()
    return params
```

- If a password is configured, it's encrypted with the time-based key and hex-encoded
- Added as a `psw` parameter alongside the command
- Applied to: `PB.SendMCUCommand`, `PB.GetState`, `PB.SetDevicePassword`, `PB.SetWifiUpdateFrequency`, `PB.SetVirtualData`, `PB.GetVirtualData`
- **NOT** applied to: `PB.GetFirmwareVersion`, `PB.GetTime`, `RPC.Ping`

### Uptime Caching

```python
async def get_uptime(self) -> float:
    now = int(time())
    if not self._last_uptime_check or now - self._last_uptime_check > 5:
        result = await self._conn.send_command("PB.GetTime", {})
        self._last_uptime = result.get("time", 0.0)
        self._last_uptime_check = now
    return self._last_uptime
```

- Uptime is cached for 5 seconds to avoid excessive `PB.GetTime` calls
- The 10-second buffer in `timed_key()` ensures the key remains valid despite caching

## Implementation Plan for Future Auth Support

To add auth support to our integration:

### 1. Detect Firmware Auth Capability
```python
# In api.py
async def supports_auth(self) -> bool:
    """Check if firmware supports authentication."""
    try:
        result = await self._rpc_get("PB.GetTime")
        return "time" in result
    except GrillConnectionError:
        return False
```

### 2. Port the Codec
Create `custom_components/grill_master/codec.py`:
- Port `timed_key()`, `encode()`, `decode()` from pytboss
- The fixed KEY constant and PADDING_LEN
- Use Python's `os.urandom()` for padding generation

### 3. Add Password to Config Flow
- Add optional password field in `config_flow.py` step 1
- Store securely in config entry data
- Validate by attempting an authenticated `PB.GetState`

### 4. Update API Client
- Add password parameter to `GrillMasterApi.__init__()`
- Add `_authenticate(params)` method matching pytboss pattern
- Add `get_uptime()` with 5-second caching
- Wrap all command calls with `_authenticate()`

### 5. Backward Compatibility
- If no password configured and `PB.GetTime` returns 404 → unauthenticated mode (current behavior)
- If password configured → authenticate all commands
- If password configured but auth fails → log error, mark entities unavailable

## Decision

Defer auth implementation until a user reports needing it. The LG1000BL Black Label ships with firmware 0.2.3 which doesn't support auth. The codec is fully documented here for when it's needed.

## Alternatives Considered

- **Option A: Implement auth now** — No way to test without a grill running newer firmware. Risk of shipping untested code.
- **Option B: Document and defer** (chosen) — Full implementation plan documented. Can be built when someone has a newer firmware device to test against.

## Consequences

- Positive: Integration stays simple and tested for the current firmware
- Positive: Complete implementation guide available when auth is needed
- Negative: Users with firmware 0.5.7+ cannot use this integration yet
