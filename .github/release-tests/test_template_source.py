"""Exercise frozen source versions and exact template archive boundaries."""

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import package_release as package
import release_version_adapter as adapter
import stage_release_assets as staging
import verify_template_source as acceptance
import version_plan as versions
import version_receipt as receipts


class TemplateSourceTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
        for name in filter(None, tracked):
            source = ROOT / name
            if source.is_file():
                destination = self.root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        for command in (["git", "init", "-q"], ["git", "add", "."],
                        ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                         "-c", "commit.gpgsign=false", "commit", "-qm", "Synthetic release fixture"]):
            subprocess.run(command, cwd=self.root, check=True, capture_output=True)
        self.sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()
        self.policy = json.loads((self.root / ".release-policy.json").read_text())
        self.config = json.loads((self.root / ".release-package.json").read_text())
        self.base = versions.read_base_version(self.root, self.policy)
        self.original = (self.root / "SOURCE_VERSION").read_bytes()
        self.environment = patch.dict(os.environ)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        os.environ.pop("RELEASE_VERSION_PLAN", None)

    def freeze(self, channel):
        (self.root / "SOURCE_VERSION").write_bytes(self.original)
        plan = versions.create_plan(self.base, channel, 7, self.sha, self.policy, 7)
        (self.root / ".release-plan.json").write_text(json.dumps(plan))
        subprocess.run([sys.executable, str(self.root / "scripts/version_plan.py"), "sync",
                        "--root", str(self.root), "--plan", ".release-plan.json"],
                       check=True, capture_output=True)
        return plan

    def test_beta_and_rc_archive_versions_receipts_and_reproducibility(self):
        for channel in ("beta", "rc"):
            with self.subTest(channel=channel):
                plan = self.freeze(channel)
                identity = versions.projections(plan)["package"]
                output = self.root / ("dist-" + channel)
                assets = package.build_package(self.root, self.base, channel, output)
                repeated = package.build_package(self.root, self.base, channel, self.root / ("repeat-" + channel))
                self.assertEqual(assets[0].read_bytes(), repeated[0].read_bytes())
                with tarfile.open(assets[0]) as archive:
                    self.assertEqual(set(archive.getnames()), {self.config["name"] + "/" + n for n in self.config["include"]})
                    self.assertEqual(archive.extractfile("dbus-service-template/SOURCE_VERSION").read().decode().strip(), identity)
                    self.assertIn(b'{{ version }}', archive.extractfile("dbus-service-template/pyproject.toml.j2").read())
                    self.assertTrue(all(member.isfile() for member in archive.getmembers()))
                staged = staging.stage(self.root, channel, [output.name + "/*"])
                inventory = [{"name": p.name, "size": p.stat().st_size,
                              "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in staged.iterdir()]
                self.assertEqual(len(receipts.verify_receipts(staged, plan, inventory, self.policy)), 1)
                self.assertTrue(receipts.verify_declared_artifacts(staged, self.policy, plan))

    def test_changed_source_version_and_wrong_channel_reject_build(self):
        self.freeze("beta")
        with self.assertRaisesRegex(ValueError, "frozen plan"):
            adapter.checked_version(self.root, self.base, "rc")
        (self.root / "SOURCE_VERSION").write_text("9.8.7")
        with self.assertRaises(ValueError):
            adapter.checked_version(self.root, self.base, "beta")
        with self.assertRaisesRegex(ValueError, "promote"):
            adapter.checked_version(self.root, self.base, "stable")

    def test_archive_extra_missing_duplicate_symlink_or_changed_bytes_rejected(self):
        output = self.root / "malformed"
        output.mkdir()
        archive_path = output / "dbus-service-template-invalid.tar.gz"
        for fault in ("extra", "missing", "duplicate", "symlink", "changed"):
            with self.subTest(fault=fault):
                names = list(self.config["include"])
                if fault == "missing":
                    names.pop()
                if fault == "extra":
                    names.append("../../outside")
                if fault == "duplicate":
                    names.append(names[0])
                with tarfile.open(archive_path, "w:gz") as archive:
                    for index, name in enumerate(names):
                        entry = tarfile.TarInfo("dbus-service-template/" + name)
                        data = (self.root / name).read_bytes() if (self.root / name).is_file() else b"bad"
                        if index == 0 and fault == "changed":
                            data += b"changed"
                        entry.size = len(data)
                        if index == 0 and fault == "symlink":
                            entry.type = tarfile.SYMTYPE
                            entry.linkname = "/outside"
                            entry.size = 0
                        archive.addfile(entry, io.BytesIO(data))
                with patch.object(acceptance.subprocess, "run") as process:
                    with self.assertRaises(ValueError):
                        acceptance.verify_archive(self.root, output)
                    process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
