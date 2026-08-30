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
import shutil
import sys
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from jinja2.exceptions import UndefinedError

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
    "python_version": "3.11",
    "include_ha_discovery": False,
    "include_dvcc": False,
    "include_gui": False,
    "version": "0.1.0",
}

# Skip the source-of-truth template files (this script + its data) and the
# copier config so the generated project is a self-contained output.
SKIP_NAMES = {"copier.yml", ".copier-answers.yml.example", "render_template.py"}

# Files that exist as templates for copier's own use; we re-render them
# directly and strip the suffix. Anything not in this set is copied as-is.
TEMPLATE_SUFFIXES = {".j2"}


def load_ctx(answers: Path | None) -> dict[str, Any]:
    """Build the render context, overlaying any answers YAML on the defaults."""
    ctx: dict[str, Any] = dict(DEFAULT_CTX)
    # cookiecutter is a legacy alias — some templates reference it.
    ctx["cookiecutter"] = ctx
    if answers and answers.is_file():
        for line in answers.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, _, val = line.partition(":")
            val = val.strip().strip('"').strip("'")
            key = key.strip()
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
        if segment.startswith("{{") and segment.endswith("}}"):
            parts.append(str(_eval_expr(segment, env, ctx)))
        else:
            parts.append(segment)
    return Path(*parts)


def _try_render(src_path: Path, env: Environment, ctx: dict[str, Any]) -> str | None:
    """Render ``src_path`` with the loader, returning ``None`` on failure."""
    loader_path = str(src_path.relative_to(TEMPLATE_ROOT))
    try:
        return env.get_template(loader_path).render(**ctx)
    except (UndefinedError, ImportError, TypeError) as exc:
        # StrictUndefined raises UndefinedError for missing vars.
        # Loader issues raise ImportError/TypeError.
        print(f"warn: render failed for {src_path}: {exc}", file=sys.stderr)
        return None


def render_tree(
    src: Path, dst: Path, env: Environment, ctx: dict[str, Any]
) -> list[Path]:
    """Copy ``src`` tree to ``dst`` rendering every template file."""
    written: list[Path] = []
    for src_path in sorted(src.rglob("*")):
        rel = src_path.relative_to(src)
        if rel.parts and rel.parts[0] in {".git", "logs"}:
            continue
        if src_path.name in SKIP_NAMES:
            continue
        rel = _render_path(rel, env, ctx)
        dst_path = dst / rel
        if src_path.is_dir():
            dst_path.mkdir(parents=True, exist_ok=True)
            continue
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        if src_path.suffix in TEMPLATE_SUFFIXES:
            dst_file = dst_path.with_name(src_path.stem)  # drop the trailing .j2
            rendered = _try_render(src_path, env, ctx)
            if rendered is None:
                shutil.copyfile(src_path, dst_file)
            else:
                dst_file.write_text(rendered)
        else:
            shutil.copyfile(src_path, dst_path)
        written.append(dst_path)
    return written


def main() -> int:
    """CLI entry: render the template into ``sys.argv[1]``."""
    if len(sys.argv) < 2:
        print("usage: render_template.py <out_dir> [answers_yaml]", file=sys.stderr)
        return 2
    out_dir = Path(sys.argv[1]).resolve()
    answers = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    ctx = load_ctx(answers)
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_ROOT)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    written = render_tree(TEMPLATE_ROOT, out_dir, env, ctx)
    py_files = [str(p.relative_to(out_dir)) for p in written if p.suffix == ".py"]
    print(json.dumps({"out_dir": str(out_dir), "python_files": py_files}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
