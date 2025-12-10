# Avalon Mini 3 – Home Assistant Integration

Custom integration to control and monitor the **Canaan Avalon Mini 3** heater/miner.

## Features

- Power on/off (soft start/stop)
- Mode select: Heating / Mining / Night
- Level select: Eco / Super
- Sensors:
  - Hashrate (MH/s)
  - Ambient temperature (TA)
  - Target temperature (TarT), as set via the Avalon app

## Installation (via HACS)

1. In Home Assistant, go to **HACS → Integrations → ⋮ → Custom repositories**.
2. Add this repo URL: `https://github.com/ajberti/ha-avalon-mini`
   - Category: `Integration`
3. Search for **"Avalon Mini 3"** in HACS integrations and install.
4. Restart Home Assistant.
5. Add this to your `configuration.yaml`:

```yaml
avalon_mini:
  host: 192.168.1.50   # IP of your Avalon Mini 3
  port: 4028           # optional, default 4028
  name: Avalon Mini 3  # friendly name
