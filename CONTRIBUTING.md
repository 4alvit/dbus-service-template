# Contributing

A Copier template and renderer for Python D-Bus services on Venus OS.

## Questions, bugs and proposals

Use [GitHub Issues](https://github.com/4alvit/dbus-service-template/issues) for questions, bug reports and feature proposals. Search existing issues first. Describe the affected version/commit, expected and actual behavior, minimal reproduction and relevant environment. Remove tokens, private endpoints, household identifiers and personal data from examples. Security vulnerabilities use the confidential process in [SECURITY.md](SECURITY.md).

Anyone may propose a change through a pull request. Discuss compatibility or architectural changes in an issue before a large implementation. Maintainers aim to acknowledge actionable reports within 14 days; security reports follow the security policy. No paid support or response-time guarantee is implied.

## Development and validation

Clone the repository, create a branch from `main`, and use the Python version and dependencies declared by the project and CI. Run from the repository root:

```sh
bash scripts/ci.sh --install
bash scripts/ci.sh
```

The local script checks template tooling, renders a disposable project, lints generated Python and runs its service/MQTT tests with coverage. It requires uv and the pinned Python toolchain from the script. Check both template-source behavior and rendered output; a passing renderer does not establish safety on live Venus OS hardware.

For a bug fix, add a regression test that fails before the fix and passes afterward. For new functionality, test normal behavior, invalid input and relevant authorization/error paths. Preserve existing checks; do not lower coverage gates or ignore findings merely to obtain a green build. Python code follows the configured formatter/linter where present and normal PEP 8 conventions otherwise. Keep shell, YAML and generated examples compatible with their declared tools.

## Review and compatibility

Keep pull requests focused and explain the problem, resulting behavior, compatibility impact and exact validation performed. Update the user-facing documentation when changing configuration, interfaces or operational behavior. Call out tests not run and their prerequisites. Maintainers review changes through GitHub pull requests and required CI; automated review is supplemental. Contributions are provided under the repository's [MIT license](LICENSE); a contributor must have the right to submit the work.

Follow `RELEASING.md` and `.release-policy.json`; this template currently uses validation-only policy. Describe template compatibility and generated-project migration separately in any source release.

## Source and interfaces

- [`src`](src)
- [`scripts/render_template.py`](scripts/render_template.py)
- [`copier.yml`](copier.yml)
- [`README.md`](README.md)
- [`docs/tutorial.md.j2`](docs/tutorial.md.j2)
- [`RELEASING.md`](RELEASING.md)

See the [OpenSSF evidence index](https://github.com/4alvit/dbus-service-template/blob/main/docs/openssf-evidence.md) for the current assessment scope and outstanding verification.
