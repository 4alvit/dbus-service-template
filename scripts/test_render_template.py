"""Regression tests for rendered files, without executing any generated workflow."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from jinja2 import Environment, StrictUndefined, UndefinedError
from render_template import DEFAULT_CTX, _render_template, render_tree


class RenderTemplateTests(unittest.TestCase):
    """Exercise the actual renderer using filesystem templates and strict Jinja."""

    def test_github_expressions_survive_rendering(self):
        """Render project values while preserving GitHub expressions byte-for-byte."""
        with TemporaryDirectory() as directory:
            source = Path(directory) / "workflow.yml.j2"
            source.write_text(
                "name: {{ project_name }}\n"
                "token: ${{ secrets.GITHUB_TOKEN }}\n"
                "asset: ${{ steps.package.outputs.path }}\n"
            )
            rendered = _render_template(
                source, Environment(undefined=StrictUndefined), DEFAULT_CTX
            )
            self.assertIn("name: My D-Bus Service", rendered)
            self.assertIn("${{ secrets.GITHUB_TOKEN }}", rendered)
            self.assertIn("${{ steps.package.outputs.path }}", rendered)

    def test_unknown_template_variable_fails(self):
        """Never silently copy an invalid, unrendered template into the output."""
        with TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.mkdir()
            (source / "bad.py.j2").write_text("value = {{ missing_variable }}")
            with self.assertRaises(UndefinedError):
                render_tree(
                    source,
                    Path(directory) / "output",
                    Environment(undefined=StrictUndefined),
                    DEFAULT_CTX,
                )

    def test_reported_paths_are_rendered_files(self):
        """Report real .py paths and honor an explicitly disabled feature."""
        with TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.mkdir()
            (source / "feature.py.j2").write_text(
                "enabled = {% if mqtt_enabled %}True{% else %}False{% endif %}\n"
            )
            output = Path(directory) / "output"
            written = render_tree(
                source,
                output,
                Environment(undefined=StrictUndefined),
                {**DEFAULT_CTX, "mqtt_enabled": False},
            )
            self.assertEqual(written, [output / "feature.py"])
            self.assertEqual(written[0].read_text(), "enabled = False")


if __name__ == "__main__":
    unittest.main()
