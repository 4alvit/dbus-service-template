# Security Policy

## Reporting a Vulnerability

Private vulnerability reporting is enabled for this repository. Use
[Report a vulnerability](https://github.com/4alvit/dbus-service-template/security/advisories/new)
to send a confidential report to the maintainers. Follow
[GitHub's private reporting instructions](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability)
if you need help submitting the report.

Include the affected version or commit, steps to reproduce, expected and actual
behavior, and potential impact. Remove access tokens, credentials and personal
data from examples. Do not disclose exploit details in public issues before
coordinating with the maintainers.

## Support and response

Security fixes target the current default branch and the latest maintained release, where releases exist. Older versions are not promised backports. Maintainers aim to acknowledge private reports within 14 days, investigate and communicate status within 60 days, and coordinate disclosure with the reporter. Confirmed vulnerabilities with a practical fix receive priority over feature work; publish an advisory and release notes that identify affected versions, mitigation and the fixed version. If a fix takes longer, keep the reporter informed without exposing confidential details.

## Deployment trust boundaries

Template values influence generated files and service behavior. Treat provided names, paths and configuration as untrusted; preserve identifier/path validation and avoid executing generated output during rendering. Generated services can interact with D-Bus and MQTT, so production operators must isolate brokers, restrict service permissions and review write paths before installation.

Use synthetic data for testing. Never attach live tokens, private keys, database exports or household telemetry to public CI artifacts. Report a suspected credential exposure privately and revoke the credential through its issuer. See [CONTRIBUTING.md](CONTRIBUTING.md) for validation and [the evidence index](docs/openssf-evidence.md) for assessment limits.
