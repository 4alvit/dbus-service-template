# System Architecture

## Overview

This document describes the system architecture for the **{{ project_name }}** D-Bus service targeting Victron Venus OS.

## Data Flow Architecture

```mermaid
graph TD
    subgraph "Hardware Layer"
        DEVICE[(Physical Device)]
        ESP[ESP32 / MCU]
        DEVICE -- UART/RS485/BLE --> ESP
    end

    subgraph "Edge Gateway"
        ESP -- MQTT --> MQTT_BROKER[(MQTT Broker)]
        MQTT_BROKER -- TLS/1883 --> MQTT_CLIENT
    end

    subgraph "Venus OS Service"
        MQTT_CLIENT[MQTT Bridge] -- Subscribe/Publish --> MQTT_BROKER
        MQTT_CLIENT --> DBUS_SERVICE[D-Bus Service]
        DBUS_SERVICE -- VeDbusService --> DBUS[System D-Bus]
        DBUS --> VRM[Victron VRM Portal]
        DBUS --> GUI[GX Touch / VRM App]
    end

    subgraph "Control & Config"
        CONFIG[Config YAML] --> MQTT_CLIENT
        CONFIG --> DBUS_SERVICE
        ENV[Environment Variables] --> MQTT_CLIENT
        ENV --> DBUS_SERVICE
    end

    style DEVICE fill:#f9f,stroke:#333
    style DBUS_SERVICE fill:#bbf,stroke:#333
    style MQTT_CLIENT fill:#bfb,stroke:#333
    style DBUS fill:#fbf,stroke:#333
```

## Component Details

### 1. Physical Device → Edge
- **Protocol**: UART, RS-485, BLE, Modbus RTU
- **Data**: Telemetry (voltage, current, power, SOC, temperature, alarms)
- **Frequency**: Configurable poll interval (default 1000ms)

### 2. MQTT Bridge (`mqtt_bridge.py`)
- **Library**: `paho-mqtt` (async, MQTT v5)
- **Features**:
  - Auto-reconnection with exponential backoff
  - Topic → D-Bus path mapping
  - SET topics for bidirectional control
  - Home Assistant MQTT Discovery (optional)
  - TLS/SSL support

### 3. D-Bus Service (`service.py`)
- **Framework**: `VeDbusService` (velib-python)
- **Paths**: Standard Victron + device-type specific
- **Methods**: GetValue, SetValue, GetStatus, Reboot
- **Signals**: PropertiesChanged (auto), custom signals

### 4. Venus OS Integration
- **D-Bus**: Registers under `com.victronenergy.<type>_<instance>`
- **VRM**: Auto-visible in VRM Portal
- **GUI**: GX Touch, VRM App, VictronConnect
- **Persistence**: systemd service, rc.local for firmware survival

## Configuration Flow

```mermaid
sequenceDiagram
    participant USER as User/Operator
    participant CONFIG as config.yaml
    participant ENV as Env Variables
    participant SERVICE as Service Start
    participant MQTT as MQTT Bridge
    participant DBUS as D-Bus Service

    USER->>CONFIG: Edit settings
    USER->>ENV: Export overrides
    SERVICE->>CONFIG: Load YAML
    SERVICE->>ENV: Apply overrides
    SERVICE->>MQTT: Initialize with config
    SERVICE->>DBUS: Initialize with config
    MQTT->>MQTT Broker: Connect & Subscribe
    DBUS->>System D-Bus: Register service
    Note over MQTT,DBUS: Bridge loop<br/>MQTT ↔ D-Bus
```

## Deployment Models

### Local Development
```mermaid
graph LR
    DEV[Developer Machine] -->|Mock D-Bus| SERVICE
    SERVICE -->|Local MQTT| BROKER[127.0.0.1:1883]
    SERVICE -->|Console| LOGS[stdout/stderr]
```

### Staging / CI
```mermaid
graph LR
    CI[GitHub Actions] -->|Build| IMAGE[Docker]
    IMAGE -->|Test| PYTEST[pytest]
    IMAGE -->|Type Check| MYPY[mypy]
    IMAGE -->|Lint| RUFF[ruff]
```

### Production (Venus OS)
```mermaid
graph LR
    IPK[.ipk Package] -->|opkg install| VENOS[Cerbo GX / Ekrano]
    VENOS -->|systemd| SERVICE_1
    SERVICE -->|D-Bus| DBUS
    VENOS -->|rc.local| PERSIST[Firmware Survive]
    SERVICE -->|MQTT| BROKER[127.0.0.1:1883]
    SERVICE -->|VRM| CLOUD[vr.victronenergy.com]
```

## Runbook

### Service Management

| Action | Command |
|--------|---------|
| Start | `systemctl start {{ project_slug }}` |
| Stop | `systemctl stop {{ project_slug }}` |
| Restart | `systemctl restart {{ project_slug }}` |
| Status | `systemctl status {{ project_slug }}` |
| Logs | `journalctl -u {{ project_slug }} -f` |

### Configuration Changes

```bash
# Edit config
vim /etc/{{ project_slug }}/config.yaml

# Reload service
systemctl restart {{ project_slug }}
```

### Debugging

```bash
# Check D-Bus registration
dbus-send --system --dest={{ service_name }}.{{ device_type }}_{{ service_instance }} \
  --print-reply / org.freedesktop.DBus.Introspectable.Introspect

# Monitor D-Bus signals
dbus-monitor --system "destination='{{ service_name }}.{{ device_type }}_{{ service_instance }}'"

# Test MQTT connectivity
mosquitto_sub -h 127.0.0.1 -t "{{ topic_prefix }}/#" -v
```

### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Service won't start | MQTT broker unreachable | Check `--mqtt-broker`, firewall |
| Not in VRM | D-Bus not registered | Check `dbus-send` introspection |
| Config not applied | YAML syntax error | Validate with `yamllint` |
| Persistence lost | Missing rc.local entry | Re-run setup script |

## Health Checks

```mermaid
graph TD
    A[Service Start] --> B{D-Bus<br/>Registered?}
    B -- No --> C[Exit 1]
    B -- Yes --> D{MQTT<br/>Connected?}
    D -- No --> E[Reconnect Loop]
    D -- Yes --> F[Main Loop]
    F --> G{Heartbeat<br/>Interval}
    G --> H[Update<br/>Connected=1]
    H --> F
```

### Health Endpoints

- **D-Bus**: `/Connected = 1` when healthy
- **MQTT**: Will message on disconnect
- **Systemd**: `systemctl is-active`

---

*Generated from dbus-service-template*