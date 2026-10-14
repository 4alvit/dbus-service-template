"""Exercise scalar answers and trusted template path rendering without I/O."""

import sys
from pathlib import Path

import atheris

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
with atheris.instrument_imports():
    from render_template import _render_path, context_from_text, render_environment

ENVIRONMENT = render_environment()
TEMPLATE_PATH = Path("src/{{ module_name }}/__init__.py.j2")


def test_one_input(data: bytes) -> None:
    text = data.decode("utf-8", errors="replace")
    try:
        context = context_from_text(text)
    except ValueError:
        return
    assert context["cookiecutter"] is context  # nosec B101 - intentional test oracle
    repeated = context_from_text(text)
    assert {k: v for k, v in context.items() if k != "cookiecutter"} == {  # nosec B101
        k: v for k, v in repeated.items() if k != "cookiecutter"
    }
    try:
        path = _render_path(TEMPLATE_PATH, ENVIRONMENT, context)
    except ValueError:
        return
    assert not path.is_absolute()  # nosec B101 - intentional test oracle
    assert len(path.parts) == 3  # nosec B101 - intentional test oracle
    assert all(part not in {"", ".", ".."} and "/" not in part and "\\" not in part  # nosec B101
               and all(ord(char) >= 32 for char in part) for part in path.parts)
    assert path == _render_path(TEMPLATE_PATH, ENVIRONMENT, repeated)  # nosec B101


if __name__ == "__main__":
    atheris.Setup(sys.argv, atheris.instrument_func(test_one_input))
    atheris.Fuzz()
