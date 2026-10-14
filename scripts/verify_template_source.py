"""Verify the published template archive by generating and testing a clean app."""

import argparse
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


def verify_archive(root: Path, assets: Path) -> None:
    """Require exact source membership and test the extracted renderer and output."""
    config = json.loads((root / ".release-package.json").read_text())
    expected = {f"{config['name']}/{name}" for name in config["include"]}
    archives = list(assets.glob("dbus-service-template-*.tar.gz"))
    if len(archives) != 1:
        raise ValueError("Expected exactly one template source archive")
    with tempfile.TemporaryDirectory(prefix="template-source-acceptance-") as temporary:
        work = Path(temporary)
        with tarfile.open(archives[0], "r:gz") as archive:
            members = archive.getmembers()
            if len(members) != len(expected) or {m.name for m in members} != expected:
                raise ValueError("Template source archive membership differs from inventory")
            for member in members:
                if not member.isfile():
                    raise ValueError("Template source archive must contain regular files")
                stream = archive.extractfile(member)
                if stream is None or stream.read() != (root / member.name.split("/", 1)[1]).read_bytes():
                    raise ValueError("Template source archive bytes differ from declared inputs")
            archive.extractall(work, filter="data")
        source = work / config["name"]
        subprocess.run([sys.executable, "-I", "-m", "venv", str(work / "venv")], check=True)
        python = work / "venv" / "bin" / "python"
        subprocess.run([
            str(python), "-I", "-m", "pip", "--isolated", "install", "--require-hashes",
            "--only-binary=:all:", "-r", str(source / ".github/requirements-template.txt"),
        ], check=True)
        subprocess.run([
            str(python), "-m", "unittest", "discover", "-s", "scripts", "-p", "test_render_template.py",
        ], cwd=source, check=True)
        generated = work / "generated"
        answers = work / "answers.yaml"
        answers.write_text("version: 9.8.7\n")
        subprocess.run([str(python), str(source / "scripts/render_template.py"), str(generated), str(answers)], check=True)
        forbidden = ["SOURCE_VERSION", "fuzz", "scripts/release.py", ".release-policy.json", ".github/workflows/fuzz.yml"]
        if any((generated / name).exists() for name in forbidden):
            raise ValueError("Repository release tooling leaked into generated application")
        subprocess.run([
            str(python), "-I", "-m", "pip", "--isolated", "install", "--no-deps", "--no-build-isolation", str(generated),
        ], check=True)
        subprocess.run([
            str(python), "-I", "-c", "from importlib.metadata import version; assert version('my-d-bus-service') == '9.8.7'",
        ], cwd=work, check=True)
        environment = dict(os.environ, PYTHONPATH=str(generated / "src"))
        subprocess.run([str(python), "-m", "pytest", str(generated / "tests"), "-q"], cwd=generated, env=environment, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assets", type=Path)
    arguments = parser.parse_args()
    verify_archive(Path(__file__).resolve().parents[1], arguments.assets.resolve())
