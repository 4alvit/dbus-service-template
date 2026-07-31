# {{ project_name }}

{{ project_description }}

Generated from [dbus-service-template](https://github.com/4alvit/dbus-service-template) using [Copier](https://copier.readthedocs.io/).

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run locally (mock D-Bus)
python -m {{ module_name }} --log-level DEBUG

# Run tests
pytest -v --cov=src/{{ module_name }}

# Lint
ruff check .
mypy src/{{ module_name }}
```

## Venus OS Deployment

Build IPK package:

```bash
docker run --rm -v "$PWD:/src" victron/venus-sdk:latest \
  make -C /src/packaging/venus-os/{{ project_slug }}
```

Install on Venus OS:

```bash
opkg install *.ipk
```

Or use SetupHelper:

```bash
bash setup INSTALL
```

## Project Structure

```
{{ cookiecutter.project_slug }/
├── .github/workflows/     # CI/CD pipelines
├── docs/                  # Documentation
├── packaging/             # Venus OS IPK packaging
│   └── venus-os/
├── src/{{ module_name }}/
│   ├── __init__.py
│   ├── __main__.py        # CLI entry point
│   ├── config.py          # Configuration (YAML + env)
│   ├── models.py          # Pydantic data models
│   ├── mqtt_bridge.py     # MQTT bridge
│   └── service.py         # D-Bus service
├── tests/
│   ├── test_service.py
│   └── test_mqtt_bridge.py
├── config.example.yaml
├── pyproject.toml
└── README.md
```

## Key Files

| File | Purpose |
|------|---------|
| `src/{{ module_name }}/service.py` | D-Bus service with VeDbusService |
| `src/{{ module_name }}/mqtt_bridge.py` | Async MQTT client with reconnection |
| `src/{{ module_name }}/config.py` | YAML config + env var overrides |
| `src/{{ module_name }}/models.py` | Pydantic models for device data |
| `packaging/venus-os/{{ project_slug }}/Makefile` | IPK build for Venus OS |

## Configuration

Copy `config.example.yaml` to `config.yaml` and adjust:

```yaml
mqtt:
  broker: "192.168.1.100"
  topic_prefix: "{{ topic_prefix }}"
  ha_discovery: {% if cookiecutter.include_ha_discovery %}true{% else %}false{% endif %}

device:
  product_name: "{{ project_name }}"
  firmware_version: "0.1.0"
  serial_number: "UNIQUE_ID"
```

Environment variables override config (prefix: `APP_`, `MQTT_`, `DEVICE_`, etc.):

```bash
export MQTT_BROKER=192.168.1.100
export DEVICE_PRODUCT_NAME="My Device"
python -m {{ module_name }}
```

## D-Bus Paths (Standard Victron)

Standard paths (auto-created):
- `/Connected` - 1=connected, 0=disconnected
- `/DeviceInstance` - Instance number
- `/ProductId`, `/ProductName`, `/FirmwareVersion`
- `/CustomName` - User-editable name

Device-type specific paths:
{% if cookiecutter.device_type == "battery" %}
- `/Soc` - State of Charge (%)
- `/Dc/0/Voltage`, `/Dc/0/Current`, `/Dc/0/Power`
- `/Capacity`, `/TimeRemaining`
- `/Alarm/*` - Alarm states
{% elif cookiecutter.device_type == "pv_inverter" %}
- `/Ac/Power`, `/Ac/L1/Voltage`, `/Ac/L1/Current`
- `/Ac/Energy/Forward`
{% elif cookiecutter.device_type == "grid_meter" %}
- `/Ac/Power`, `/Ac/L1/Voltage`, `/Ac/L1/Current`
- `/Ac/Energy/Forward`, `/Ac/Energy/Reverse`
{% elif cookiecutter.device_type == "tank" %}
- `/Level`, `/Capacity`, `/Remaining`
{% elif cookiecutter.device_type == "temperature" %}
- `/Temperature`
{% else %}
- `/Value`, `/Unit`
{% endif %}

## DVCC Integration

{% if cookiecutter.include_dvcc %}
Dynamic Voltage/Current Control paths:
- `/Dc/0/MaxChargeCurrent`
- `/Dc/0/MaxDischargeCurrent`
- `/Dc/0/MaxChargeVoltage`
- `/Dc/0/AllowCharge`
- `/Dc/0/AllowDischarge`

Use `service.set_max_charge_current(50.0)` to limit charging.
{% else %}
DVCC not enabled. Enable in template with `include_dvcc=true`.
{% endif %}

## MQTT Topics

Default mappings (customizable in code):

| MQTT Topic | D-Bus Path |
|------------|------------|
| `{{ topic_prefix }}/voltage` | `/Dc/0/Voltage` |
| `{{ topic_prefix }}/current` | `/Dc/0/Current` |
| `{{ topic_prefix }}/soc` | `/Soc` |
| `{{ topic_prefix }}/.../set` | Write to D-Bus |

SET topics (e.g., `topic/set`) allow MQTT → D-Bus control.

{% if cookiecutter.include_ha_discovery %}
## Home Assistant Discovery

Auto-publishes sensor configs on connect:
- Topic: `homeassistant/sensor/{unique_id}/config`
- Retained messages with device info
{% endif %}

## Testing

```bash
# Unit tests
pytest tests/ -v

# With coverage
pytest --cov=src/{{ module_name }} --cov-report=html

# Type check
mypy src/{{ module_name }}
```

## License

{{ license_type }} License - see [LICENSE](LICENSE)

## Documentation

- [System Architecture](./.github/docs/system-architecture.md) - Data flow diagrams, runbook
- [ADR](.github/docs/adr-001.md) - Architecture Decision Records