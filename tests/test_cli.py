"""CLI smoke tests for cosmograph."""

import pytest
from typer.testing import CliRunner
from pathlib import Path
from cosmograph.cli import app

runner = CliRunner()


class TestCLI:
    """CLI smoke tests."""

    def test_help_command(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "cosmograph" in result.stdout.lower() or "generate" in result.stdout.lower()

    def test_version_command(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "cosmograph" in result.stdout.lower()

    def test_generate_help(self):
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "extractor" in result.stdout.lower() or "-e" in result.stdout

    def test_stats_help(self):
        result = runner.invoke(app, ["stats", "--help"])
        assert result.exit_code == 0
        assert "input" in result.stdout.lower() or "path" in result.stdout.lower()

    def test_serve_help(self):
        result = runner.invoke(app, ["serve", "--help"])
        assert result.exit_code == 0
        assert "port" in result.stdout.lower()


class TestGenerateCommand:
    """Tests for the generate command."""

    def test_generate_legal_document(self, tmp_path):
        # Create test input
        input_file = tmp_path / "test.txt"
        input_file.write_text("ARTICLE I - TEST\nSECTION 1. Content.")
        output_dir = tmp_path / "output"

        result = runner.invoke(app, [
            "generate",
            str(input_file),
            "-e", "legal",
            "-o", str(output_dir),
            "--no-open"  # Don't open browser in tests
        ])

        assert result.exit_code == 0
        assert (output_dir / "index.html").exists()
        assert (output_dir / "index.html").stat().st_size > 0

    def test_generate_text_document(self, tmp_path):
        input_file = tmp_path / "test.md"
        input_file.write_text("# Header\nSome content.")
        output_dir = tmp_path / "output"

        result = runner.invoke(app, [
            "generate",
            str(input_file),
            "-e", "text",
            "-o", str(output_dir),
            "--no-open"
        ])

        assert result.exit_code == 0
        assert (output_dir / "index.html").exists()

    def test_generate_generic_document(self, tmp_path):
        input_file = tmp_path / "test.txt"
        input_file.write_text("John Smith visited. John Smith returned.")
        output_dir = tmp_path / "output"

        result = runner.invoke(app, [
            "generate",
            str(input_file),
            "-e", "generic",
            "-o", str(output_dir),
            "--no-open"
        ])

        assert result.exit_code == 0
        assert (output_dir / "index.html").exists()

    def test_generate_with_title(self, tmp_path):
        input_file = tmp_path / "test.txt"
        input_file.write_text("Test content")
        output_dir = tmp_path / "output"

        result = runner.invoke(app, [
            "generate",
            str(input_file),
            "-t", "My Custom Title",
            "-o", str(output_dir),
            "--no-open"
        ])

        assert result.exit_code == 0
        html = (output_dir / "index.html").read_text()
        assert "My Custom Title" in html

    def test_generate_html_only(self, tmp_path):
        input_file = tmp_path / "test.txt"
        input_file.write_text("Test content")
        output_dir = tmp_path / "output"

        result = runner.invoke(app, [
            "generate",
            str(input_file),
            "--html-only",
            "-o", str(output_dir),
            "--no-open"
        ])

        assert result.exit_code == 0
        assert (output_dir / "index.html").exists()
        # CSV files should not be created with --html-only
        assert not (output_dir / "graph_nodes.csv").exists()

    def test_generate_directory_input(self, tmp_path):
        # Create multiple test files
        input_dir = tmp_path / "docs"
        input_dir.mkdir()
        (input_dir / "file1.txt").write_text("ARTICLE I - TEST")
        (input_dir / "file2.txt").write_text("ARTICLE II - OTHER")
        output_dir = tmp_path / "output"

        result = runner.invoke(app, [
            "generate",
            str(input_dir),
            "-e", "legal",
            "-o", str(output_dir),
            "--no-open"
        ])

        assert result.exit_code == 0
        assert (output_dir / "index.html").exists()

    def test_nonexistent_file_error(self, tmp_path):
        result = runner.invoke(app, [
            "generate",
            str(tmp_path / "nonexistent.txt"),
            "--no-open"
        ])
        # Should fail gracefully
        assert result.exit_code != 0 or "error" in result.stdout.lower() or "not found" in result.stdout.lower()

    def test_empty_directory_error(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = runner.invoke(app, [
            "generate",
            str(empty_dir),
            "-p", "*.txt",
            "--no-open"
        ])
        # Should fail with "no files" message
        assert result.exit_code != 0 or "no files" in result.stdout.lower()


class TestStatsCommand:
    """Tests for the stats command."""

    def test_stats_nonexistent_file(self, tmp_path):
        result = runner.invoke(app, [
            "stats",
            str(tmp_path / "nonexistent")
        ])
        assert result.exit_code != 0

    def test_stats_with_generated_files(self, tmp_path):
        # First generate some output
        input_file = tmp_path / "test.txt"
        input_file.write_text("ARTICLE I - TEST\nSECTION 1. Content.")
        output_dir = tmp_path / "output"

        runner.invoke(app, [
            "generate",
            str(input_file),
            "-e", "legal",
            "-o", str(output_dir),
            "--no-open"
        ])

        # Now test stats on the output
        result = runner.invoke(app, [
            "stats",
            str(output_dir)
        ])

        assert result.exit_code == 0
        assert "nodes" in result.stdout.lower() or "graph" in result.stdout.lower()
