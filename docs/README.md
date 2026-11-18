# Documentation

A scaffold for building a new Venus OS D-Bus service: the generator's design, the
quality baseline it enforces and how a template release is versioned.

## Design

- [Architecture, interfaces and security design](architecture.md) — how the CLI renders the files and where defaults are applied.
- [Roadmap](roadmap.md) — what the generator already covers and what is planned.

## Quality

- [Quality checks and reproducible build inputs](quality-and-build.md) — the Python and uv versions and the hash-locked template install.
- [OpenSSF Best Practices evidence](openssf-evidence.md) — what the public questionnaire assesses.

## Releases

- [Template source releases](template-source-releases.md) — `SOURCE_VERSION` and why it is independent of consuming services.
- [CI and release operations](release-workflow.md) — `.release-policy.json` and the required status.
- [CI orchestration](CI-ORCHESTRATION.md) — how the quality gate and release pipeline divide the events.
- [Version plans and manifest synchronization](VERSIONING.md) — the versioning opt-in.
- [RC fuzz qualification](fuzzing.md) — the illustrated RC fuzzing process.
- [Fuzzing release candidates](rc-fuzzing.md) — the reusable bounded fuzz workflow.
- [Release read recovery and rerun validation](release-read-safety.md) — the two fixes carried from the shared toolkit.
- [Early final-build runner check](runner-preflight.md) — why the check runs before the final build.
