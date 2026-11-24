# Allpowers HACS Integration

Home Assistant custom component supporting Allpowers Batteries and Solar Generators

## R2500 V2 UPS status

**UPS Status** is a read-only Home Assistant sensor for devices identified as `AP R2500 V2.0`.

- **Mains bypass** (`bypass`): The station reports mains power and its AC output is enabled.
- **On battery** (`battery`): The station reports battery power and its AC output is enabled. This can mean standalone use or backup operation after mains power is lost.
- **AC output off** (`ac_output_off`): The station reports that its AC output is disabled.

The sensor becomes unavailable when the required Bluetooth readings are missing, unrecognized, or stale. Mains bypass is derived from the reported power source and output state. [R2500 V2 protocol reference](https://github.com/borro/allpowers-bridge/blob/ce9fbf9eb4b363323b273ca24ec3fa8ffd6f1385/core/src/AllpowersModels.h#L92-L133)

## Upstream archival notice

I no longer have any access to Allpowers batteries so am unable to develop or test any new hardware or fix any reported issues.

Please fork this repo to continue development.
