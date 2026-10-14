# OpenSSF Best Practices evidence

The [public questionnaire](https://www.bestpractices.dev/projects/15298) assesses
this repository's renderer, release tooling and maintained service templates.
Generated applications have independent versions, maintainers, configurations
and security assessments. This page does not itself award any badge.

- [Project purpose, acquisition and usage](../README.md)
- [Contribution process and test requirements](../CONTRIBUTING.md)
- [License](../LICENSE), [governance](../GOVERNANCE.md), [code of conduct](../CODE_OF_CONDUCT.md)
- [Architecture, interfaces and security design](architecture.md)
- [Confidential vulnerability reporting and support](../SECURITY.md)
- [Roadmap](roadmap.md), [changelog](../CHANGELOG.md) and [release ownership](../RELEASING.md)
- [Quality/build commands and evidence limitations](quality-and-build.md)
- [Dated assessment receipt](evidence/assessment-2026-10-13.json)

The source repository is publicly maintained in Git; GitHub Issues and pull
requests preserve reports, discussion and changes. The 2026-10-13 owner attestation
covers knowledge of secure design/common implementation weaknesses and confirms
no outside-GitHub bug reports, enhancement requests or vulnerability reports in
the preceding 12 months. The GitHub audit found no ordinary issues, project
advisories, open Dependabot alerts or open secret-scanning alerts. Scans do not
prove absolute absence of vulnerabilities or secrets.

Five existing Scorecard process recommendations are distinct from exploitable
runtime findings: pinned dependencies, Best Practices completion, code review,
maintenance and branch protection. Rulesets currently require a reviewed PR,
CI gate and CodeQL; no settings are weakened to improve a score. The assessment
records those recommendations openly rather than claiming zero scanner output.

Known Silver gaps include the absence of a backup maintainer/access-recovery
mechanism, insufficient whole-project coverage evidence, no quantified 50%
regression ratio, visible deprecation warnings, unsigned release artifacts,
no verified cross-environment reproducible build, and no full accessibility or
internationalization audit. Credential-free plaintext MQTT remains an explicit
local/isolated-network option. These are not represented as satisfied requirements.
