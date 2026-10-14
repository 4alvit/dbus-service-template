# Architecture, interfaces and security design

## Source generator

The CLI reads scalar answers, overlays explicit defaults and renders the files
listed in `template-files.json` with Jinja2 `StrictUndefined`. It preserves GitHub
Actions expressions for their later intended execution. Filesystem paths reject
traversal, symlinked ancestors and duplicate destinations. Output must be a new
directory; the generator never removes an existing application. Rendering can
leave partial new output on an error and callers must discard it before retrying.

Answer types, Python identifiers, shell-safe package identifiers, D-Bus names,
ports, instances, runtime and license choices are validated before output creation.
Strings cannot contain control characters or quote/backslash/backtick/dollar/brace
source delimiters. The template source is executable trusted project code, not
an untrusted template sandbox. Do not execute a downloaded or modified template
until its source and origin have been reviewed. The renderer has no network server.

## Generated service

`config.py` loads local YAML with `safe_load`, overlays environment values and
constructs Pydantic models. `models.py` describes device data. `service.py` exposes
D-Bus paths and callbacks using firmware bindings where available, with local
mocks for tests. `mqtt_bridge.py` maps configured MQTT topics into those paths
and optionally publishes Home Assistant discovery. The CLI owns startup and
shutdown. `setup` is an explicit administrative deployment operation using
persistent `/data` and daemontools; generation does not invoke it.

Local configuration, environment, generated source and the installer are trusted
administrative inputs. MQTT messages cross a network trust boundary. Rejecting
invalid UTF-8 and payloads above 64 KiB bounds basic parsing work but does not
replace topic ACLs, physical constraints, command authorization or device testing.
Telemetry and `/set` writers can influence D-Bus state: use a dedicated broker
identity, least-privilege publish/subscribe ACLs and an isolated network.

Credentialed MQTT rejects plaintext, including if configuration is mutated before
client construction. Optional TLS uses Python/OpenSSL certificate and hostname
verification, TLS >= 1.2, security level 3, AEAD ciphers and ephemeral ECDHE/DHE.
This requires approximately RSA >= 3072 bits or ECC >= 256 bits, exceeding the exact
OpenSSF minimum of RSA 2048 / ECC 224 bits even where OpenSSL rounds strength; operator client keys
and CA certificates must meet that platform policy. TLS 1.3 uses platform modern
suites. No custom crypto algorithm, password-verifier database or security random
number generator is implemented. TLS randomness is provided by OpenSSL. Runtime
passwords are outbound broker credentials, not password hashes for user login.
Protect local credential files with restrictive permissions and rotate them with
the broker. There is no application-specific credential vault or live rotation API.

## Delivery and assurance limits

Source and release manifests are obtained through authenticated GitHub HTTPS or
SSH. SHA-256 manifests detect changed bytes relative to a trusted manifest; they
are not independent release signatures. Dependencies are external FLOSS components
(Python, Jinja2, Pydantic, Paho MQTT, PyYAML, Click and build/test tools). CI's
Python requirements use exact hashes; generated applications specify compatible
ranges and must select and monitor their own deployment lock.

Layered tests, lint, Bandit on tooling and rendered Python, CodeQL and dependency
scans support the security argument. Evidence is linked from [the assessment
index](openssf-evidence.md). No penetration test, complete absence of defects,
physical-safety certification or inherited downstream badge is claimed.
