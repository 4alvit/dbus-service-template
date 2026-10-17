# Changelog

## [0.1.3] - 2026-10-17

### Changed

- Clarify where RC fuzz safeguards execute and add illustrated process and result guides.

### Upgrade

Template behavior and supported answer formats are unchanged from 0.1.2. Generate into a fresh directory, compare the result with existing applications, and preserve local configuration for rollback.

### Security

No new runtime security fix is claimed. Existing answer validation, template checks and source-bound RC fuzzing remain required; generated applications still require target-device acceptance.

## [0.1.2] - 2026-10-14

### Changed

- Validate each public release candidate with bounded, network-isolated fuzz campaigns against its exact source revision.
- Require positive engine execution counts, instrumented production code and validated seed corpora; retain source-bound reports and diagnostic evidence.
- Run deterministic seed and configuration checks in ordinary CI without starting mutation campaigns on betas.

### Upgrade

Use the existing installation procedure, preserve local configuration and keep the previous accepted package for rollback. This maintenance release updates release validation and does not change the application configuration format. Deployment and applicable device or integration acceptance remain separate from publication.

### Security

RC publication rejects absent or invalid source-bound fuzz reports. The fuzz runner bounds corpus paths, file types and size. No application vulnerability or new target-device acceptance is claimed by these tooling changes.

## [0.1.1]

### Added

- Publish reproducible template-source beta and RC archives with frozen version receipts.
- Qualify RCs with bounded Linux answer-parser and output-path campaigns.
- Declare generated-application inputs explicitly so release tooling cannot enter generated apps.

- Document the template identity, supported generation path, governance and scoped security assessment.
- Validate typed source answers before writing output; reject code/shell delimiters and unsupported license choices.
- Require TLS for broker credentials, constrain TLS ciphers and reject oversized or non-UTF-8 MQTT messages.
- Security-scan rendered Python in CI as well as repository tooling.
- Reject malformed answer lines and keep invalid MQTT payloads from affecting bounded reconnect backoff.

### Upgrade

- Existing credentialed MQTT configurations must enable verified TLS and use the broker's TLS port and a certificate meeting OpenSSL security level 3 (normally RSA 3072
  or ECC 256 bits). Source answers containing unsupported code delimiters must be simplified.
- Extract the source archive, install its hashed template requirements, and render into a new directory.
- The template source version is separate from the generated application version; review generated changes before any deployment.

### Security

- Reserved context aliases and colliding output paths are rejected. Generated files exclude repository release and fuzz infrastructure.
- Tests use synthetic answers and temporary output paths; device firmware, broker authentication and hardware behavior require separate acceptance.

## 0.1.0 - 2026-09-12

- First tagged source release of the service template and renderer.
- Generate executable native Venus OS setup and service scripts with persistent
  `/data` deployment and `svc`/`svstat` supervision.
- Separate runtime service directories from package sources so repeated installs
  preserve active supervisor state; keep boot hooks before a conventional `exit 0`.
- Document offline dependencies and distinguish generated native services from
  unsupported legacy packaging examples.

This project generates source for a separately configured service. Releasing the
template does not create or install an additional service on a GX device.
