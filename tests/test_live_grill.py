"""Live integration test against a real LG1000BL grill.

This test hits the actual grill over the network. Only run when the grill
is powered on and connected to WiFi.

Run: python tests/test_live_grill.py [grill-ip]
Default IP: 192.168.1.100
"""

import asyncio
import json
import sys
import os

# Reuse the same module loading trick from test_decoder.py
import types
import importlib.util

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Stub out HA dependencies
_pkg = types.ModuleType("custom_components")
_pkg.__path__ = [os.path.join(_root, "custom_components")]
sys.modules["custom_components"] = _pkg

_sub = types.ModuleType("custom_components.grill_master")
_sub.__path__ = [os.path.join(_pkg.__path__[0], "grill_master")]
_sub.__package__ = "custom_components.grill_master"
sys.modules["custom_components.grill_master"] = _sub

_const = types.ModuleType("custom_components.grill_master.const")
_const.STATUS_PREFIX = "FE0B"
_const.TEMP_PREFIX = "FE0C"
_const.CMD_POWER_OFF = "FE0102FF"
_const.CMD_LIGHT_ON = "FE0201FF"
_const.CMD_LIGHT_OFF = "FE0200FF"
_const.DEFAULT_TIMEOUT = 5
sys.modules["custom_components.grill_master.const"] = _const

# Load decoder
_decoder_path = os.path.join(_sub.__path__[0], "decoder.py")
spec = importlib.util.spec_from_file_location(
    "custom_components.grill_master.decoder", _decoder_path
)
decoder = importlib.util.module_from_spec(spec)
decoder.__package__ = "custom_components.grill_master"
spec.loader.exec_module(decoder)
sys.modules["custom_components.grill_master.decoder"] = decoder

# Load api
_api_path = os.path.join(_sub.__path__[0], "api.py")
spec2 = importlib.util.spec_from_file_location(
    "custom_components.grill_master.api", _api_path
)
api_mod = importlib.util.module_from_spec(spec2)
api_mod.__package__ = "custom_components.grill_master"
spec2.loader.exec_module(api_mod)

import aiohttp


async def run_live_tests(host: str) -> tuple[int, int]:
    """Run live tests against the grill.

    Returns (passed, failed) count.
    """
    passed = 0
    failed = 0

    async with aiohttp.ClientSession() as session:
        api = api_mod.GrillMasterApi(session, host)

        # ------------------------------------------------------------------
        # Test 1: Ping
        # ------------------------------------------------------------------
        print("\n1. RPC.Ping")
        try:
            result = await api.ping()
            assert result is True, f"Ping returned {result}"
            print(f"   PASS - Grill reachable at {host}")
            passed += 1
        except Exception as e:
            print(f"   FAIL - {e}")
            failed += 1
            print("\n   Cannot reach grill. Aborting remaining tests.")
            return passed, failed

        # ------------------------------------------------------------------
        # Test 2: Firmware version
        # ------------------------------------------------------------------
        print("\n2. PB.GetFirmwareVersion")
        try:
            fw = await api.get_firmware_version()
            assert fw and fw != "unknown", f"Got: {fw}"
            print(f"   PASS - Firmware: {fw}")
            passed += 1
        except Exception as e:
            print(f"   FAIL - {e}")
            failed += 1

        # ------------------------------------------------------------------
        # Test 3: Sys.GetInfo
        # ------------------------------------------------------------------
        print("\n3. Sys.GetInfo")
        try:
            info = await api.get_info()
            assert "id" in info, "No 'id' field"
            assert "mac" in info, "No 'mac' field"
            assert "fw_version" in info, "No 'fw_version' field"
            print(f"   PASS - Device: {info['id']}, MAC: {info['mac']}, FW: {info['fw_version']}")
            passed += 1
        except Exception as e:
            print(f"   FAIL - {e}")
            failed += 1

        # ------------------------------------------------------------------
        # Test 4: PB.GetState returns expected structure
        # ------------------------------------------------------------------
        print("\n4. PB.GetState (raw)")
        try:
            state = await api.get_state()
            assert "sc_11" in state, "No 'sc_11' in response"
            assert "sc_12" in state, "No 'sc_12' in response"
            assert state["sc_11"].startswith("FE0B"), f"sc_11 doesn't start with FE0B: {state['sc_11'][:8]}"
            assert state["sc_12"].startswith("FE0C"), f"sc_12 doesn't start with FE0C: {state['sc_12'][:8]}"
            print(f"   PASS - sc_11: {len(state['sc_11'])//2} bytes, sc_12: {len(state['sc_12'])//2} bytes")
            passed += 1
        except Exception as e:
            print(f"   FAIL - {e}")
            failed += 1

        # ------------------------------------------------------------------
        # Test 5: Decode FE0C temperatures
        # ------------------------------------------------------------------
        print("\n5. Decode FE0C (temperatures)")
        try:
            state = await api.get_state()
            temps = decoder.decode_temperatures(state["sc_12"])
            assert temps is not None, "decode_temperatures returned None"
            assert "grill_temp" in temps, "No grill_temp"
            assert "grill_set_temp" in temps, "No grill_set_temp"
            assert "is_fahrenheit" in temps, "No is_fahrenheit"
            print(f"   PASS - Grill: {temps['grill_temp']}F, Set: {temps['grill_set_temp']}F, "
                  f"P1: {temps['p1_temp']}, P2: {temps['p2_temp']}, "
                  f"Fahrenheit: {temps['is_fahrenheit']}")
            passed += 1
        except Exception as e:
            print(f"   FAIL - {e}")
            failed += 1

        # ------------------------------------------------------------------
        # Test 6: Decode FE0B status
        # ------------------------------------------------------------------
        print("\n6. Decode FE0B (status)")
        try:
            state = await api.get_state()
            status = decoder.decode_status(state["sc_11"])
            assert status is not None, "decode_status returned None"
            assert "module_is_on" in status, "No module_is_on"
            assert "light_state" in status, "No light_state"
            print(f"   PASS - Power: {status['module_is_on']}, Light: {status['light_state']}, "
                  f"Fan: {status.get('fan_state')}, Errors: "
                  f"[hi_temp={status['high_temp_err']}, fan={status['fan_err']}, "
                  f"hot={status['hot_err']}, motor={status['motor_err']}, "
                  f"pellets={status['no_pellets']}]")
            passed += 1
        except Exception as e:
            print(f"   FAIL - {e}")
            failed += 1

        # ------------------------------------------------------------------
        # Test 7: Full coordinator-style merge
        # ------------------------------------------------------------------
        print("\n7. Merged state (coordinator simulation)")
        try:
            state = await api.get_state()
            status = decoder.decode_status(state["sc_11"])
            temps = decoder.decode_temperatures(state["sc_12"])
            merged = {}
            if status:
                merged.update(status)
            if temps:
                merged.update(temps)
            assert len(merged) > 10, f"Merged state only has {len(merged)} fields"
            print(f"   PASS - {len(merged)} fields in merged state")
            # Print full state for inspection
            print("   Full state:")
            for k, v in sorted(merged.items()):
                if not k.startswith("_"):
                    print(f"     {k}: {v}")
            passed += 1
        except Exception as e:
            print(f"   FAIL - {e}")
            failed += 1

    return passed, failed


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.100"

    print("=" * 60)
    print(f"Grill Master Live Test - {host}")
    print("=" * 60)

    passed, failed = asyncio.run(run_live_tests(host))

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")

    if failed:
        sys.exit(1)
    else:
        print("\nAll live tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
