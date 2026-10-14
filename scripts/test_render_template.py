"""Regression tests for rendered files, without executing any generated workflow."""

import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from jinja2 import UndefinedError

from render_template import (
    DEFAULT_CTX,
    _render_template,
    context_from_text,
    render_environment,
    render_tree,
    source_files,
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

    def test_existing_output_is_never_deleted_or_overwritten(self):
        with TemporaryDirectory() as directory:
            source, output = Path(directory) / "source", Path(directory) / "output"
            source.mkdir()
            output.mkdir()
            retained = output / "important.txt"
            retained.write_text("keep me")
            with self.assertRaises(ValueError):
                render_tree(source, output, render_environment(), DEFAULT_CTX)
            self.assertEqual(retained.read_text(), "keep me")

    def test_path_answers_cannot_escape_output(self):
        with TemporaryDirectory() as directory:
            source, output = Path(directory) / "source", Path(directory) / "output"
            source.mkdir()
            (source / "{{ module_name }}.py.j2").write_text("value = 1")
            for value in ("../outside", "/tmp/outside", "safe/../../outside", "..\\outside"):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    render_tree(source, output, render_environment(), {**DEFAULT_CTX, "module_name": value})
                self.assertFalse(output.exists())

    def test_symlink_source_cannot_copy_private_files(self):
        with TemporaryDirectory() as directory:
            source, output = Path(directory) / "source", Path(directory) / "output"
            source.mkdir()
            private = Path(directory) / "private-key"
            private.write_text("synthetic secret")
            (source / "key").symlink_to(private)
            with self.assertRaises(ValueError):
                render_tree(source, output, render_environment(), DEFAULT_CTX)
            self.assertFalse(output.exists())

    def test_git_checkout_copies_only_tracked_files(self):
        with TemporaryDirectory() as directory:
            source, output = Path(directory) / "source", Path(directory) / "output"
            source.mkdir()
            subprocess.run(["git", "init", "--quiet", str(source)], check=True)
            (source / "tracked.py.j2").write_text("value = 1")
            (source / "private-key").write_text("synthetic secret")
            subprocess.run(["git", "-C", str(source), "add", "tracked.py.j2"], check=True)
            render_tree(source, output, render_environment(), DEFAULT_CTX)
            self.assertEqual({path.name for path in output.iterdir()}, {"tracked.py"})

    def test_tracked_file_under_symlinked_parent_is_rejected(self):
        with TemporaryDirectory() as directory:
            source, output = Path(directory) / "source", Path(directory) / "output"
            source.mkdir()
            nested = source / "nested"
            nested.mkdir()
            tracked = nested / "file.txt"
            tracked.write_text("tracked source")
            subprocess.run(["git", "init", "--quiet", str(source)], check=True)
            subprocess.run(["git", "-C", str(source), "add", "nested/file.txt"], check=True)
            tracked.unlink()
            nested.rmdir()
            private = Path(directory) / "private"
            private.mkdir()
            (private / "file.txt").write_text("synthetic private data")
            nested.symlink_to(private, target_is_directory=True)
            with self.assertRaises(ValueError):
                render_tree(source, output, render_environment(), DEFAULT_CTX)
            self.assertFalse(output.exists())

    def test_source_archive_excludes_local_environment_and_badge(self):
        with TemporaryDirectory() as directory:
            source, output = Path(directory) / "source", Path(directory) / "output"
            source.mkdir()
            (source / ".venv-ci").mkdir()
            (source / ".venv-ci" / "local.py").write_text("local = True")
            (source / ".env").write_text("TOKEN=synthetic")
            (source / ".bestpractices.json").write_text("{}")
            (source / "tracked.py.j2").write_text("value = 1")
            render_tree(source, output, render_environment(), DEFAULT_CTX)
            self.assertEqual({path.name for path in output.iterdir()}, {"tracked.py"})


    def test_inventory_excludes_repository_tools_in_checkout_and_archive(self):
        for checkout in (False, True):
            with self.subTest(checkout=checkout), TemporaryDirectory() as directory:
                source = Path(directory) / "source"
                source.mkdir()
                (source / "app.py.j2").write_text("answer = 42\n")
                (source / "release.py").write_text("raise RuntimeError('repository tool')")
                (source / "fuzz").mkdir()
                (source / "fuzz" / "target.py").write_text("raise RuntimeError('fuzzer')")
                (source / "template-files.json").write_text(json.dumps({"files": ["app.py.j2"]}))
                if checkout:
                    subprocess.run(["git", "init", "--quiet", str(source)], check=True)
                    subprocess.run(["git", "-C", str(source), "add", "."], check=True)
                output = Path(directory) / "output"
                render_tree(source, output, render_environment(), DEFAULT_CTX)
                self.assertEqual({p.name for p in output.iterdir()}, {"app.py"})

    def test_inventory_rejects_ambiguous_and_escaping_paths(self):
        with TemporaryDirectory() as directory:
            source = Path(directory)
            for files in (["../escape"], ["/tmp/escape"], ["a", "a"], [1], []):
                with self.subTest(files=files):
                    (source / "template-files.json").write_text(json.dumps({"files": files}))
                    with self.assertRaises(ValueError):
                        source_files(source)

    def test_two_source_files_cannot_overwrite_one_output(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.mkdir()
            (source / "same.py").write_text("first = True")
            (source / "same.py.j2").write_text("second = True")
            with self.assertRaisesRegex(ValueError, "collide"):
                render_tree(source, Path(directory) / "output", render_environment(), DEFAULT_CTX)
            self.assertFalse((Path(directory) / "output").exists())

    def test_pure_context_parser_preserves_alias_and_scalar_behavior(self):
        ctx = context_from_text("# comment\nversion: 9.8.7\nmqtt_enabled: false\nservice_instance: 42\n")
        self.assertIs(ctx["cookiecutter"], ctx)
        self.assertEqual(ctx["version"], "9.8.7")
        self.assertEqual(ctx["service_instance"], 42)
        self.assertFalse(ctx["mqtt_enabled"])
        with self.assertRaisesRegex(ValueError, "reserved"):
            context_from_text("cookiecutter: replacement")


if __name__ == "__main__":
    unittest.main()
