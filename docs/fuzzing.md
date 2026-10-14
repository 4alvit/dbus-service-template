# RC fuzz qualification

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
