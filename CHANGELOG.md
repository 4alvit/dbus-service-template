# Changelog

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
