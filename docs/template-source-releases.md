# Template source releases

`SOURCE_VERSION` versions this repository's distributable template. It is independent
of the `version` answer used by generated application metadata. A frozen release
plan overlays only `SOURCE_VERSION`; `pyproject.toml.j2` keeps the user-selected
application version. The default application version remains 0.1.0.

Each beta or RC publishes a deterministic `dbus-service-template-<version>.tar.gz`
with the explicit `.release-package.json` inputs: all application templates,
`template-files.json`, the renderer and its regression tests, the hash-locked
renderer/test dependencies, license, release notes and source documentation.
`template-files.json` alone selects generated application files. Release scripts,
repository policies, fuzzing infrastructure and repository badge claims never
become generated application files.

The build downloads the plan allocated by the release controller, synchronizes
its declared version field, builds once, then validates the exact archive bytes.
Acceptance checks exact archive membership and regular file types, extracts into
a temporary directory, creates a fresh virtual environment, installs the shipped
hash-locked dependencies, runs the extracted renderer tests, generates an app with
version 9.8.7, installs that app, checks installed package metadata, and runs its
unit tests. The unusual application version proves separation from the source
release version. Version receipts and SHA-256 manifests bind those built assets
to the source commit and frozen plan.

The beta channel checks source distribution and installation. RC additionally
requires the bounded Linux Atheris campaign described in [fuzzing.md](fuzzing.md).
Both are prereleases. A successful result validates source generation and mocked
software contracts; no broker connection, D-Bus service, installer or device is
started. Hardware compatibility and a generated service's deployment acceptance
remain separate responsibilities. Stable publication is not part of this change.

To inspect a downloaded archive, verify its published manifest first, extract it
into a new directory, and run the shipped renderer with Python 3.12 and Jinja2:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r .github/requirements-template.txt
.venv/bin/python -m unittest discover -s scripts -p test_render_template.py
.venv/bin/python scripts/render_template.py ../generated-app answers.yaml
```

Use a new output directory. Inspect the rendered source and configuration before
any later deployment. Never run an installer as part of source qualification.
