# Quality checks and reproducible build inputs

Use Python 3.12.13 and uv. The local install uses the same hash-locked template
and Bandit requirements as CI:

```sh
bash scripts/ci.sh --install
bash scripts/ci.sh
.venv-ci/bin/python -m unittest discover -s .github/security-tests -p test_bandit_discovery.py
.venv-ci/bin/python scripts/workflow_contracts.py
.venv-ci/bin/python -m unittest discover -s .github/workflow-tests -p 'test_*.py'
.venv-ci/bin/python -m unittest discover -s .github/release-tests -p 'test_*.py'
.venv-ci/bin/python -m bandit -r scripts fuzz -ll
```

The local entry point lints Python tooling, runs renderer tests, generates a new
temporary project, lints and security-scans its Python and runs the generated
service tests with coverage. It never installs a Venus OS service. The tests
include synthetic loopback TLS peers to verify rejection of a trusted RSA 2048
certificate and acceptance of a trusted RSA 3072 certificate at security level 3.
They send no MQTT traffic and require the OpenSSL CLI. CI supplies this tool;
a developer machine without it records an explicit skipped test.

Generated tests also exercise the successful platform-import branch using a
strict `VeDbusService` test double: constructor arguments, registration order,
existing-path updates, callbacks, shutdown and CLI construction. Separate tests
cover absent platform dependencies, tank settings and incremental battery
telemetry through the MQTT bridge. These tests verify API use without connecting
to a live D-Bus broker; they do not replace target-device acceptance.

CI also runs CodeQL for Python/Actions, dependency review, Bandit and Trivy for
high/critical dependencies, secrets and configuration. Generated Python must be
scanned explicitly because the maintained source templates have `.j2` suffixes.
The existing source Bandit scan has 30 low-severity subprocess review notices:
those calls use argument arrays, trusted local tools and no shell evaluation.
Two rejected absolute-path test fixtures have narrow B108 annotations; no tested
path is opened. Medium/high findings are not suppressed to pass the checks.

## Packaging and installation acceptance

The release pipeline packages the explicit `.release-package.json` inventory,
then runs `scripts/verify_template_source.py` on the built archive. That check
compares exact file membership and bytes, extracts into a fresh directory,
installs hashed dependencies in a fresh virtualenv, runs the extracted renderer,
installs a generated application versioned 9.8.7 and runs its tests. This checks
that source and generated-application versions remain separate. The result is a
source archive, not an executable for a specific GX device.

For an unreleased local base version, source packaging can be exercised without
publishing a tag or release (use the value from `SOURCE_VERSION`):

```sh
.venv-ci/bin/python scripts/package_release.py 0.1.1 beta --output /tmp/template-package-check
.venv-ci/bin/python scripts/verify_template_source.py /tmp/template-package-check
```

The destination must be empty. Without a frozen release plan this creates a local base-version archive for
inspection only; it does not allocate a candidate identity, publish or promote a
release. Stable packaging correctly refuses to rebuild promoted bytes. Actual publication must
follow [RELEASING.md](../RELEASING.md) and its acceptance/approval gates.

## Coverage and limitations

The dated [assessment receipt](evidence/assessment-2026-10-13.json) records actual
counts. Generated-service statement coverage is a subset: repository release
scripts, shell installers, every feature combination and real device bindings
are not included in that denominator. No whole-project 80% statement-coverage
claim is made. Hardware, actual broker ACLs and physical safety behavior require
separate acceptance by a generated application's operator.

Ruff's configured diagnostics pass. Known Paho callback API v1 deprecation
warnings remain visible; maximum warnings-as-errors is not claimed. The scaffold
includes a mypy configuration, but this assessment does not claim a clean strict
type-check across all generated and release code. No exhaustive regression ratio,
performance benchmark or accessibility audit has been established.

RC-only Atheris fuzzing is configured for scalar parsing and path rendering.
Replaying its seed corpus in unit tests is not a completed fuzz campaign and does
not exercise every new source-answer type constraint. This assessment does not
claim a newly completed fuzz campaign or first-party native-memory sanitizer run.
