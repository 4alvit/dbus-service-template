# Template validation and packaging

This repository supplies a project template. PRs and nightly runs validate the
renderer and generated project. It has no application release version, so
nightly/beta/RC/stable publication is disabled by the release policy.

Run local checks with `bash scripts/ci.sh --install`, then `bash scripts/ci.sh`.
Run `bash scripts/ci.sh security` after installing the Trivy CLI for the same
high severity Python/dependency/secret gates.

To build an explicitly versioned source bundle for a downstream consumer, run
`bash scripts/package-release.sh 1.0.0 rc --output /path/to/empty-directory`.
This creates an archive and SHA256SUMS locally and publishes nothing. Choose
the version explicitly for that downstream use; it is not an application release.
