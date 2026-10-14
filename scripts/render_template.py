"""
Render this copier template to a real project directory.

Copier v9 leaves ``.j2`` suffixes and does not understand ``cookiecutter.X``
references (this template predates its copier migration). To generate a
working project we do a full Jinja render of the template tree ourselves
and write the output to ``<out_dir>`` with the ``.j2`` suffix stripped.

Usage:
    python scripts/render_template.py <out_dir> [answers_yaml]
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CTX: dict[str, Any] = {
    "project_name": "My D-Bus Service",
    "project_description": "D-Bus service for Venus OS",
    "project_slug": "my-d-bus-service",
    "module_name": "my_d_bus_service",
    "class_name": "MyDBusService",
    "service_name": "com.victronenergy.mydbusservice",
    "device_type": "generic",
    "service_instance": 0,
    "mqtt_enabled": True,
    "mqtt_broker_default": "127.0.0.1",
    "mqtt_port_default": 1883,
    "topic_prefix": "my-d-bus-service",
    "venus_os_package": True,
    "github_org": "4alvit",
    "author_name": "4alvit",
    "author_email": "noreply@4alvit.dev",
    "license_type": "MIT",
    "python_version": "3.12",
    "include_ha_discovery": False,
    "include_dvcc": False,
    "include_gui": False,
    "version": "0.1.0",
}

# Skip the source-of-truth template files (this script + its data) and the
# copier config so the generated project is a self-contained output.
SKIP_NAMES = {
    "copier.yml", ".copier-answers.yml.example", "render_template.py", "test_render_template.py",
    ".bestpractices.json", "openssf-evidence.md", ".coverage",
}

# Files that exist as templates for copier's own use; we re-render them
# directly and strip the suffix. Anything not in this set is copied as-is.
TEMPLATE_SUFFIXES = {".j2"}


def render_environment() -> Environment:
    """Escape HTML/XML while preserving Python, YAML and shell source text."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_ROOT)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        autoescape=select_autoescape(
            enabled_extensions=("html", "htm", "xml"),
            default_for_string=False,
            default=False,
        ),
    )


def load_ctx(answers: Path | None) -> dict[str, Any]:
    """Build the render context, overlaying any answers YAML on the defaults."""
    return context_from_text(answers.read_text() if answers and answers.is_file() else "")


def context_from_text(text: str) -> dict[str, Any]:
    """Parse the renderer's existing scalar answer syntax without filesystem I/O."""
    ctx: dict[str, Any] = dict(DEFAULT_CTX)
    # cookiecutter is a legacy alias — some templates reference it.
    ctx["cookiecutter"] = ctx
    if text:
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, _, val = line.partition(":")
            val = val.strip().strip('"').strip("'")
            key = key.strip()
            if key == "cookiecutter":
                raise ValueError("cookiecutter is a reserved context alias")
            if val.lower() in ("true", "false"):
                val = val.lower() == "true"
            else:
                try:
                    val = int(val)
                except ValueError:
                    pass
            ctx[key] = val
    return ctx


def _eval_expr(expr: str, env: Environment, ctx: dict[str, Any]) -> Any:
    """Evaluate a single ``{{ var }}`` expression via Jinja."""
    return env.from_string(expr).render(**ctx)


def _render_path(rel: Path, env: Environment, ctx: dict[str, Any]) -> Path:
    """Replace Jinja expressions in path segments (e.g. ``{{ module_name }}``)."""
    parts: list[str] = []
    for segment in rel.parts:
        if "{{" in segment:
            parts.append(str(_eval_expr(segment, env, ctx)))
        else:
            parts.append(segment)
    if any(
        not part or part in {".", ".."} or "/" in part or "\\" in part
        or any(ord(char) < 32 for char in part)
        for part in parts
    ):
        raise ValueError("Template answers must not create unsafe output paths")
    return Path(*parts)


def _render_template(src_path: Path, env: Environment, ctx: dict[str, Any]) -> str:
    """Render Jinja variables while preserving literal GitHub Actions expressions."""
    source = re.sub(
        r"\$\{\{.*?\}\}",
        lambda match: "{% raw %}" + match.group() + "{% endraw %}",
        src_path.read_text(),
        flags=re.DOTALL,
    )
    # StrictUndefined must fail instead of silently shipping an unrendered file.
    # from_string has no filename, so apply the policy to the rendered filename.
    # This also enables escaping for future .html.j2 or .xml.j2 templates.
    if callable(env.autoescape):
        output_name = src_path.name.removesuffix(".j2")
        env = env.overlay(autoescape=env.autoescape(output_name))
    return env.from_string(source).render(**ctx)


def inventory_files(src: Path, manifest: Path) -> list[Path]:
    """Read the explicit generated-application inventory."""
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError("Template inventory must be a regular file")
    data = json.loads(manifest.read_text())
    names = data.get("files") if isinstance(data, dict) else None
    if not isinstance(names, list) or not names:
        raise ValueError("Template inventory must contain files")
    if any(not isinstance(name, str) for name in names) or len(set(names)) != len(names):
        raise ValueError("Template inventory must contain unique paths")
    paths = []
    for name in names:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or str(path) != name:
            raise ValueError("Template inventory paths must be canonical and relative")
        paths.append(src / path)
    return sorted(paths)


def source_files(src: Path) -> list[Path]:
    """Select the inventory; legacy fixtures fall back to tracked source files."""
    manifest = src / "template-files.json"
    if manifest.exists() or manifest.is_symlink():
        return inventory_files(src, manifest)
    if (src / ".git").exists():
        result = subprocess.check_output(
            ["git", "-C", str(src), "ls-files", "--cached", "-z"]
        )
        paths = [src / name for name in result.decode().split("\0") if name]
    else:
        paths = []
        excluded = {".git", ".venv", ".venv-ci", "venv", "__pycache__",
                    ".pytest_cache", ".ruff_cache", ".mypy_cache", "logs",
                    "dist", "build", "release-dist", "private"}
        for root, dirs, files in os.walk(src, followlinks=False):
            dirs[:] = [name for name in dirs if name not in excluded
                       and not (Path(root) / name).is_symlink()]
            paths.extend(Path(root) / name for name in files)
    return sorted(path for path in paths if path.name not in SKIP_NAMES
                  and path.name not in {".env", "secrets.yaml", "secrets.yml"}
                  and not path.name.endswith((".pyc", ".pyo")))


def render_tree(
    src: Path, dst: Path, env: Environment, ctx: dict[str, Any]
) -> list[Path]:
    """Render to a new directory without reading symlinks or local checkout state."""
    paths = source_files(src)
    if dst.exists() or dst.is_symlink():
        raise ValueError("Output must be a new directory; existing files are never removed")
    plans = []
    destinations: set[Path] = set()
    for src_path in paths:
        current = src
        for component in src_path.relative_to(src).parts:
            current /= component
            if current.is_symlink():
                raise ValueError("Template source cannot contain symlinked ancestors")
        if not src_path.is_file():
            raise ValueError("Template source must contain only regular files")
        rel = _render_path(src_path.relative_to(src), env, ctx)
        if src_path.suffix in TEMPLATE_SUFFIXES:
            rel = rel.with_name(rel.stem)
        if rel.is_absolute() or not (dst / rel).resolve().is_relative_to(dst.resolve()):
            raise ValueError("Template output path escapes the destination")
        if rel in destinations:
            raise ValueError("Template files collide at the same output path")
        destinations.add(rel)
        plans.append((src_path, dst / rel))
    dst.mkdir(parents=True, exist_ok=False)
    written: list[Path] = []
    for src_path, dst_path in plans:
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        if src_path.suffix in TEMPLATE_SUFFIXES:
            dst_path.write_text(_render_template(src_path, env, ctx))
        else:
            shutil.copyfile(src_path, dst_path)
        shutil.copymode(src_path, dst_path)
        written.append(dst_path)
    return written


def main() -> int:
    """CLI entry: render the template into ``sys.argv[1]``."""
    if len(sys.argv) < 2:
        print("usage: render_template.py <out_dir> [answers_yaml]", file=sys.stderr)
        return 2
    out_dir = Path(sys.argv[1]).absolute()
    answers = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    ctx = load_ctx(answers)
    env = render_environment()
    written = render_tree(TEMPLATE_ROOT, out_dir, env, ctx)
    py_files = [str(p.relative_to(out_dir)) for p in written if p.suffix == ".py"]
    print(json.dumps({"out_dir": str(out_dir), "python_files": py_files}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
