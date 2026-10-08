# OpenSSF Best Practices evidence

This is an evidence index for the OpenSSF Best Practices Passing self-assessment. It is not an assertion that a badge has been awarded or that every criterion is satisfied. The public badge service is the authority for an awarded status.

## Project and participation

A Copier template and renderer for Python D-Bus services on Venus OS.

The project is developed publicly in [Git](https://github.com/4alvit/dbus-service-template) under the [MIT license](../LICENSE). Its source, issue tracker and pull requests are available without a paid account. [Contribution instructions](../CONTRIBUTING.md) describe reporting, changes, coding conventions, tests and review. The [security policy](../SECURITY.md) provides a confidential vulnerability-reporting path, support scope, response targets and deployment boundaries.

## User and interface documentation

- [`README.md`](../README.md)
- [`docs/tutorial.md.j2`](../docs/tutorial.md.j2)
- [`RELEASING.md`](../RELEASING.md)

## Source, testing and analysis

- [`src`](../src)
- [`scripts/render_template.py`](../scripts/render_template.py)
- [`copier.yml`](../copier.yml)

- [Test suite](../tests) and [CI workflows](../.github/workflows)
- [Local CI entry point](../scripts/ci.sh)
- [CodeQL analysis](../.github/workflows/codeql.yml)
- [Dependency update configuration](../.github/dependabot.yml)

The local script checks template tooling, renders a disposable project, lints generated Python and runs its service/MQTT tests with coverage. It requires uv and the pinned Python toolchain from the script. Check both template-source behavior and rendered output; a passing renderer does not establish safety on live Venus OS hardware.

CI results are evidence for the tested revision and environment, not proof of safe production or hardware operation. Check the current default-branch runs and unresolved security findings before answering the analysis criteria. Fuzzing, coverage completeness and independent penetration testing must be supported by actual runs; ordinary unit tests must not be presented as those activities.

## Changes and releases

Follow `RELEASING.md` and `.release-policy.json`; this template currently uses validation-only policy. Describe template compatibility and generated-project migration separately in any source release. The [release policy](../.release-policy.json) records automation behavior. A new release must identify its source revision and explain notable changes; security fixes must identify relevant advisories when known.

## Criteria still requiring verification

Before submitting or updating the questionnaire, verify the actual project-specific record: responses to bug and enhancement reports, vulnerability reports in every supported channel, release-note history, unresolved scanner findings, dependency status and required review settings. The primary maintainer must personally confirm knowledge of secure design and common implementation vulnerabilities. A confirmation about another repository does not establish these answers here.

Assess transport encryption, credential storage and privilege limits against the implementation and deployment documented in [SECURITY.md](../SECURITY.md). Do not mark a requirement satisfied solely because a policy says it should be. Record justified non-applicability only where the actual architecture supports it. No paid certification, blanket compliance guarantee or third-party audit is claimed.

## Implementation evidence audited on 2026-10-08 UTC

11 renderer regression tests and 51 generated-project tests passed (26 additional subtests); the generated application had 65% statement coverage across 902 statements. The current change adds regressions for output preservation, path traversal, symlinks, local files and assessment metadata exclusion. Generated Paho callbacks currently emit two deprecation warnings; this known compatibility item does not disable compiler/lint diagnostics. Coverage is statement coverage, not a claim of complete branch or hardware coverage. The unit commands are documented in CONTRIBUTING; the coverage measurement used coverage.py 7.10.7 for the voice projects and the hash-locked pytest-cov toolchain for the generated template.

The supported Python 3.12 runtime was checked with `ssl.create_default_context()`: Python 3.12.14 / OpenSSL 3.5.8 reported a TLS 1.2 minimum, security level 2, required certificate validation, hostname checks and at least 128-bit symmetric ciphers. Offered TLS 1.2 key exchanges were ephemeral ECDHE/DHE; TLS 1.3 was also enabled. The application uses the standard context without enabling obsolete protocol versions or lowering its security level. These are runtime configuration observations, not measurements of a production endpoint. Operators must retain an updated supported runtime and validate their own ingress and devices. See [Python's TLS documentation](https://docs.python.org/3.12/library/ssl.html#ssl.create_default_context).

The generated MQTT client creates its TLS context with `ssl.create_default_context()` and can load an operator CA/client certificate without disabling server verification. MQTT TLS is an operator option; the default local-broker plaintext transport must remain inside a trusted isolated network. The template does not create a user-password database or implement cryptographic primitives. Certificates and private keys remain operator-managed and must satisfy the documented platform policy.

In a Git checkout the renderer now reads only tracked source, rejects source symlinks and answer-derived path traversal, and requires a new output directory. Source archives exclude common local environments and credential files. A template's OpenSSF questionnaire is never copied into its generated project.

No dedicated fuzzer or dynamic taint tool is currently claimed. The optional dynamic-analysis criterion is explicitly unmet, and complete branch coverage/maximum warning strictness are not claimed. Existing tests execute with assertions enabled. No confirmed medium/high exploitable issue discovered by these runtime tests remains unresolved; future findings follow SECURITY.md.
