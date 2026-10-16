# RC fuzz qualification

See the [illustrated RC fuzzing process and verified rollout results](https://github.com/victron-venus/venus-os-ci-toolkit/blob/main/docs/rc-fuzzing-results.md)
for the shared release flow, evidence requirements and a dated cross-project
snapshot. The project-specific scope and reproduction guidance below still apply.

The `render-context` target invokes the production `context_from_text` scalar
answer parser and `_render_path` with a trusted fixed template path. It verifies
that the legacy cookiecutter alias is preserved, parsing/rendering are deterministic,
and every accepted output has exactly three relative, non-traversing path segments
without separators or control characters. Invalid reserved aliases and unsafe path
answers are ordinary rejected inputs. The fuzzer never evaluates user-provided
Jinja source or writes generated files.

`.github/fuzz.json` runs Atheris on Linux for 60 seconds with inputs bounded to
4096 bytes. Dependencies are hash-locked; corpus seeds are synthetic scalar,
Unicode, traversal and alias examples. PR checks replay seeds, while the RC gate
requires the actual engine campaign and its source-bound report. A crash blocks
publication and should be minimized, fixed in production code, and retained as a
regression seed. Beta publication does not imply that the RC campaign ran.

Local Linux invocation after installing the declared environment:

```sh
python3 -m venv .fuzz-venv
.fuzz-venv/bin/python -m pip install --require-hashes --only-binary=:all: -r .github/requirements-fuzz.txt
.fuzz-venv/bin/python fuzz/fuzz_render_context.py -max_len=4096 -max_total_time=60 fuzz/corpus/render-context
```

Renderer filesystem safety, archive membership and clean generated application
installation are independently tested by the source acceptance command. Fuzzing
is bounded software testing; it provides no hardware or deployment certification.


## Deterministic preflight in ordinary CI

For relevant changes in a public repository, the existing CI configuration
contract job installs the hash-locked Python 3.12 fuzz dependencies, runs
`pip check`, and replays the committed corpus with Atheris `-runs=0`.
This is deterministic seed replay: it does not start the timed mutation
campaign. Timed fuzzing remains exclusive to release candidates. The shared
preflight has a four-minute total budget, including dependency setup.

The `preflight-paths` entries in `.github/fuzz.json` select the relevant
production, dependency and harness changes. Shared contract, manifest and
workflow changes also trigger this check; missing comparison history runs
the check conservatively. Unrelated changes can skip this extra replay.

Before replay, the shared helper verifies that the following declarations
refer to project-local Python functions already instrumented by the
harness. Missing import instrumentation fails the check instead of
silently counting executions with incomplete feedback:

- `render_template.context_from_text`
- `render_template._render_path`

Update these declarations when production functions move or are renamed.
They prove that the selected code is instrumented; they do not prove
exhaustive path coverage. Keep positive and rejected-input corpus cases
and independent semantic assertions alongside the existing unit tests.
