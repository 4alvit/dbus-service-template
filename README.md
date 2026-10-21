# dbus-service-template

[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/15298/badge)](https://www.bestpractices.dev/projects/15298)
[![Fuzzing: RC only](https://img.shields.io/badge/fuzzing-RC_only-blue)](docs/fuzzing.md)

A Python source generator for D-Bus services on Victron Venus OS. The template
provides typed configuration, device models, an optional MQTT bridge, Home
Assistant discovery, tests and native daemontools installation scaffolding.
Generated applications need review, configuration and their own hardware testing.

The OpenSSF badge assesses **this repository**, including its renderer, release
tooling and maintained service templates. Generated services do not inherit the
badge, release version, governance or security promises of this repository.

## Generate and test a service

Use Python **3.12.x**; CI pins 3.12.13. Clone a reviewed tag or source commit from
[this repository](https://github.com/4alvit/dbus-service-template), then:

```sh
python3.12 -m venv .venv-ci
.venv-ci/bin/python -m pip install --require-hashes --only-binary=:all: -r .github/requirements-template.txt
.venv-ci/bin/python scripts/render_template.py generated-service .copier-answers.yml.example
.venv-ci/bin/python -m pip install --no-deps --no-build-isolation ./generated-service
.venv-ci/bin/python -m pytest generated-service/tests/
```

The output directory **must not exist**. The renderer does not remove old output.
It accepts the simple scalar answers shown in `.copier-answers.yml.example`, not
a general YAML document. Set identifiers explicitly; project names do not
implicitly recompute module, class, topic or package names. Supported names and
source-delimiter restrictions are explained in [the tutorial](docs/tutorial.md.j2).
Use the supplied renderer; direct `copier copy` is not the validated generation
path. `copier.yml` describes the available questions for compatibility and review.

The sample answers generate `my_battery_monitor`. Omit the answers argument for
`my_d_bus_service`. A generated project's `README.md` and `docs/tutorial.md`
contain its own usage and installation instructions. Only the explicit
[`template-files.json`](template-files.json) inventory becomes generated output.
The template and its generated license text are MIT; another license requires a
separate reviewed license-template change.

## Interfaces and operating boundaries

- `scripts/render_template.py OUTPUT [ANSWERS]` generates source without running
  the generated application or installer. Nonzero exit means generation failed;
  discard a partially written new directory before retrying.
- Configuration uses `config.example.yaml`, `load_config()` and `DEVICE_`,
  `MQTT_`, `BATTERY_`, `PV_`, `GRID_`, `TANK_` and `TEMP_` environment prefixes.
- Generated `service.py` exposes standard D-Bus identity paths and device-specific
  values. `set_path()` changes a path and callbacks publish corresponding values.
  The MQTT bridge maps telemetry and `/set` topics to configured D-Bus paths.
  Temperature mode maps `<topic_prefix>/temperature` to `/Temperature`;
  `<topic_prefix>/temperature/set` uses the same path. Generic mode retains
  `<topic_prefix>/value` and `<topic_prefix>/unit` for `/Value` and `/Unit`.
- The CLI requires the real `dbus`, GLib and `vedbus` libraries. It creates all
  service paths before registering the bus name. The in-memory fallback is for
  tests and direct library use; the CLI exits when platform dependencies are absent.
- Battery voltage, current and derived power start as unknown. Updating voltage
  or current recomputes power from both latest readings, including zero readings.
  Tank `tank.capacity`, `/Capacity` and `/Remaining` use cubic metres (1 m³ =
  1000 litres); battery capacity uses amp-hours.
- Credentialed MQTT requires TLS. TLS verifies the server hostname and certificate
  chain, uses TLS 1.2 or later and forward-secret modern ciphers at OpenSSL security level 3 (normally RSA 3072 or ECC 256-bit certificates). Plaintext MQTT
  remains available only for credential-free, isolated test/local networks.
  Broker ACLs must restrict who can publish telemetry and control commands.
- Incoming MQTT payloads must be valid UTF-8 and no larger than 64 KiB. These
  checks are not a device-specific validation or physical safety policy; validate
  operating ranges and permitted commands in each generated application.

Venus OS packages use daemontools and persistent `/data`, not systemd or the old
OpenWrt IPK recipe. Use the firmware's Python and matching D-Bus/GI libraries.
Do not install development dependencies on a device or replace its OS interpreter.
The [architecture and security design](docs/architecture.md) describes trust
boundaries, limitations and extension points.

## Development, releases and participation

Run `bash scripts/ci.sh --install`, then `bash scripts/ci.sh` for the local lint,
renderer, generated-service and security checks. See [quality and build
instructions](docs/quality-and-build.md) for complete commands and coverage scope.

[`SOURCE_VERSION`](SOURCE_VERSION) versions the template source separately from
the generated application's `version` answer. [Releases](https://github.com/4alvit/dbus-service-template/releases)
identify immutable tags; [CHANGELOG.md](CHANGELOG.md) explains changes and migration.
The [release policy](RELEASING.md), [source release contract](docs/template-source-releases.md)
and [release runbook](docs/release-workflow.md) distinguish beta, RC and stable.
An RC runs additional bounded fuzzing. Passing CI does not authorize device deployment.

Report bugs, propose features or ask questions through [GitHub Issues](https://github.com/4alvit/dbus-service-template/issues).
Read [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md),
[GOVERNANCE.md](GOVERNANCE.md), [the roadmap](docs/roadmap.md) and
[SECURITY.md](SECURITY.md) for review, conduct and confidential vulnerability reporting.
[The OpenSSF evidence index](docs/openssf-evidence.md) records verified behavior and
remaining requirements; this project does not currently claim a Silver badge.

## License

[MIT](LICENSE). Third-party Python tools and libraries keep their own licenses.
