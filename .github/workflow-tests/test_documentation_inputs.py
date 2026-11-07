"""Keep mandatory package inputs checked on the lightweight documentation path."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "docs_package_release", ROOT / "scripts/package_release.py"
)
PACKAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGE)


class DocumentationInputsTests(unittest.TestCase):
    def test_committed_package_inventory_is_present(self):
        config = json.loads((ROOT / ".release-package.json").read_text())
        _, selected = PACKAGE.package_inputs(ROOT, config)
        for name in selected:
            with self.subTest(path=name):
                self.assertTrue((ROOT / name).is_file(), name)
                self.assertFalse((ROOT / name).is_symlink(), name)

    def test_missing_required_document_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                patch.object(
                    PACKAGE.subprocess, "check_output", return_value=b"README.md\0"
                ),
                self.assertRaisesRegex(ValueError, "Missing required runtime input"),
            ):
                PACKAGE.package_inputs(root, {"include": ["README.md"]})


if __name__ == "__main__":
    unittest.main()
