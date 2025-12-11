# 📦 Avalon Mini 3 — Home Assistant Integration

A custom Home Assistant integration for monitoring and controlling the **Canaan Avalon Mini 3** heater–miner.  
Supports full status monitoring, power control, mode switching presented as native HA entities.

> ⚡️ Built to work seamlessly with HACS and the Home Assistant UI (config flow, no YAML required).

---

## ✨ Features

### 🔧 Control the miner
- **Power On / Off** (soft power control)
- **Mode selection:** Heating / Mining / Night
- **Level selection:** Eco / Super

### 📊 Live system monitoring
- **Hashrate (TH/s)** — automatically converted from Avalon MH/s output  
- **Room Temperature (°C)** using `ITemp` (inlet sensor)  
- **Target Temperature (°C)** using `TarT`  
- **Power Draw (W)** parsed from `PS[...]`  
- **Future-ready:** hashboard temp, fan speeds, and more can be added

### 🧠 Smart state sync
- Entities auto-update when values change **via the Avalon mobile app**
- Power detection uses `SYSTEMSTATU` (`In Work`, `In Init`, `In Idle`)
- Power switch includes a **grace period** to avoid UI bounce on startup/shutdown

### 🖥 Dashboard-ready
Compatible with all Lovelace card types:
- Gauges  
- Graphs  
- Entities  
- Automations  
- Custom dashboards  

---

## 📥 Installation (via HACS)

### 1. Add the repository
In Home Assistant:

1. Go to **HACS → Integrations**
2. Click **⋮ → Custom repositories**
3. Add: https://github.com/ajberti/ha-avalon-mini
   
Category: **Integration**

---

### 2. Install the integration
- Search in HACS for **Avalon Mini 3**
- Click **Install**
- Restart Home Assistant

---

### 3. Add the integration
Go to:

**Settings → Devices & Services → Add Integration → "Avalon Mini 3"**

Enter:

- **Host** (IP address of your Avalon Mini 3)  
- **Port** (default: `4028`)  
- **Name** (friendly name)  

No YAML configuration required.

---

## 🧩 Entities Provided

### **Switches**
| Entity | Description |
|--------|-------------|
| `switch.<name>_power` | Soft power control |

### **Selects**
| Entity | Options |
|--------|---------|
| `select.<name>_mode` | Heating / Mining / Night |
| `select.<name>_level` | Eco / Super |

### **Sensors**
| Entity | Description |
|--------|-------------|
| `sensor.<name>_hashrate` | Hashrate (TH/s) |
| `sensor.<name>_room_temperature` | Room/inlet temperature (ITemp) |
| `sensor.<name>_power_draw` | Estimated power draw (W) |

---

## 🖼 Example Dashboard (Lovelace)

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Avalon Mini Controls
    entities:
      - switch.avalon_mini_power
      - select.avalon_mini_mode
      - select.avalon_mini_level

  - type: horizontal-stack
    cards:
      - type: gauge
        entity: sensor.avalon_mini_room_temperature
        name: Room Temp
        min: 0
        max: 100
      - type: gauge
        entity: sensor.avalon_mini_hashrate
        name: Hashrate (TH/s)
        min: 0
        max: 60

  - type: statistics-graph
    title: Power Draw (24h)
    entities:
      - sensor.avalon_mini_power_draw
    days_to_show: 1
    chart_type: line


