#!/usr/bin/env bash
# Install once with --install, then run the same lint/type/test commands used by CI.
set -euo pipefail
cd "$(dirname "$0")/.."
python_bin="${CI_PYTHON:-$PWD/.venv-ci/bin/python}"
if [[ "${1:-}" == --install ]]; then
  uv venv .venv-ci --python 3.12.13
  uv pip install --python "$python_bin" ruff jinja2 pyyaml pytest pytest-asyncio pytest-cov pytest-mock paho-mqtt pydantic pydantic-settings click mypy bandit==1.9.2
  exit 0
fi
if [[ ! -x "$python_bin" ]]; then
  echo 'Run bash scripts/ci.sh --install first, or set CI_PYTHON to a prepared interpreter.' >&2
  exit 1
fi
if [[ "${1:-}" == security ]]; then
  "$python_bin" -m bandit -r . -lll -x .git,.venv,.venv-ci,tests,release-dist,dist,build
  command -v trivy >/dev/null || { echo 'Install Trivy to run the same release dependency/secret scan locally.' >&2; exit 1; }
  trivy fs --scanners vuln,secret,misconfig --severity HIGH,CRITICAL --exit-code 1 --skip-dirs .git,.venv,.venv-ci,release-dist,dist,build .
  exit 0
fi
"$python_bin" -m ruff check scripts/
"$python_bin" -m unittest discover -s scripts -p 'test_*.py' -v
generated="$(mktemp -d)"
trap 'rm -rf "$generated"' EXIT
"$python_bin" scripts/render_template.py "$generated/project"
"$python_bin" -m ruff check "$generated/project/src/"
PYTHONPATH="$generated/project/src" "$python_bin" -m pytest "$generated/project/tests/" --cov=my_d_bus_service
