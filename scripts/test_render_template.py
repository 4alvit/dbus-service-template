"""Regression tests for rendered files, without executing any generated workflow."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from jinja2 import UndefinedError

from render_template import (
    DEFAULT_CTX,
    _render_template,
    render_environment,
    render_tree,
)


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
                source, render_environment(), DEFAULT_CTX
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
                    render_environment(),
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
                render_environment(),
                {**DEFAULT_CTX, "mqtt_enabled": False},
            )
            self.assertEqual(written, [output / "feature.py"])
            self.assertEqual(written[0].read_text(), "enabled = False\n")

    def test_source_code_characters_remain_literal(self):
        """HTML escaping must not corrupt generated source operators or quotes."""
        value = "1 < 2 and 'x' != '&'"
        with TemporaryDirectory() as directory:
            for suffix in ("py", "yaml", "sh", "md"):
                with self.subTest(suffix=suffix):
                    source = Path(directory) / f"source.{suffix}.j2"
                    source.write_text("{{ expression }}\n")
                    rendered = _render_template(
                        source, render_environment(), {"expression": value}
                    )
                    self.assertEqual(rendered, value + "\n")

    def test_html_and_xml_outputs_escape_values(self):
        """Select escaping by the output suffix, including templates read as strings."""
        with TemporaryDirectory() as directory:
            for suffix in ("html", "htm", "xml"):
                with self.subTest(suffix=suffix):
                    source = Path(directory) / f"page.{suffix}.j2"
                    source.write_text("{{ value }}")
                    rendered = _render_template(
                        source, render_environment(), {"value": '<tag attr="value">&'}
                    )
                    self.assertEqual(rendered, "&lt;tag attr=&#34;value&#34;&gt;&amp;")

    def test_native_setup_preserves_mode_and_rendered_path(self):
        """Keep incoming native installer modes and mixed literal/template paths."""
        with TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.mkdir()
            installer = source / "prefix-{{ project_slug }}" / "setup.j2"
            installer.parent.mkdir()
            installer.write_text("#!/bin/sh\nexit 0\n")
            installer.chmod(0o755)
            output = Path(directory) / "output"
            written = render_tree(source, output, render_environment(), DEFAULT_CTX)
            expected = output / "prefix-my-d-bus-service" / "setup"
            self.assertEqual(written, [expected])
            self.assertEqual(expected.stat().st_mode & 0o777, 0o755)
            self.assertEqual(expected.read_text(), "#!/bin/sh\nexit 0\n")


if __name__ == "__main__":
    unittest.main()
