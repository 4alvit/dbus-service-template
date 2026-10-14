"""Replay synthetic context seeds with the same production-code fuzz oracle."""

import contextlib
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class FuzzSeedTests(unittest.TestCase):
    def test_synthetic_seeds(self):
        root = Path(__file__).resolve().parents[1]
        fake = types.SimpleNamespace(instrument_imports=contextlib.nullcontext)
        with patch.dict(sys.modules, {"atheris": fake}):
            spec = importlib.util.spec_from_file_location("fuzz_render_context", root / "fuzz/fuzz_render_context.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for seed in sorted((root / "fuzz/corpus/render-context").iterdir()):
                with self.subTest(seed=seed.name):
                    module.test_one_input(seed.read_bytes())
