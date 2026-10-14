# Changelog

## [0.1.1]

### Added

- Publish reproducible template-source beta and RC archives with frozen version receipts.
- Qualify RCs with bounded Linux answer-parser and output-path campaigns.
- Declare generated-application inputs explicitly so release tooling cannot enter generated apps.

### Upgrade

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
