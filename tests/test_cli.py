"""Issue 3 — Tests for the SRG CLI."""
from __future__ import annotations

from pathlib import Path

from srg.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "srg" / "examples"


class TestValidate:
    def test_valid_graph(self, capsys) -> None:
        rc = main(["validate", str(EXAMPLES / "subnet_scorer.yaml")])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Valid: subnet_scorer" in out
        assert "7 nodes" in out
        assert "10 edges" in out
        assert "extract_features" in out

    def test_valid_simple_graph(self, capsys) -> None:
        rc = main(["validate", str(EXAMPLES / "repo_risk.yaml")])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Valid: repo_risk" in out

    def test_missing_file(self, capsys) -> None:
        rc = main(["validate", "nonexistent.yaml"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "Load error" in err

    def test_invalid_graph(self, tmp_path, capsys) -> None:
        # Agentic node missing output_schema
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text(
            "name: bad\n"
            "nodes:\n"
            "  - id: n1\n"
            "    kind: agentic\n"
            "    inputs: [x]\n"
            "    outputs: [y]\n"
            "edges: []\n"
        )
        rc = main(["validate", str(bad_yaml)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "Invalid" in err


class TestDiff:
    def test_identical_graphs(self, capsys) -> None:
        path = str(EXAMPLES / "subnet_scorer.yaml")
        rc = main(["diff", path, path])
        assert rc == 0
        out = capsys.readouterr().out
        assert "No differences" in out

    def test_different_graphs(self, capsys) -> None:
        rc = main(["diff",
                    str(EXAMPLES / "validator_scorer.yaml"),
                    str(EXAMPLES / "repo_risk.yaml")])
        assert rc == 0
        out = capsys.readouterr().out
        # Should show structural differences
        assert "node" in out or "edge" in out or "->" in out

    def test_modified_graph(self, tmp_path, capsys) -> None:
        # Copy and modify
        original = EXAMPLES / "validator_scorer.yaml"
        modified = tmp_path / "modified.yaml"
        content = original.read_text().replace("validator_scorer", "modified_scorer")
        modified.write_text(content)

        rc = main(["diff", str(original), str(modified)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "name" in out

    def test_missing_file(self, capsys) -> None:
        rc = main(["diff", "nonexistent.yaml", str(EXAMPLES / "repo_risk.yaml")])
        assert rc == 1
        err = capsys.readouterr().err
        assert "Load error" in err


class TestRun:
    def test_run_without_registry(self, capsys) -> None:
        # Will fail because deterministic nodes need registered functions
        rc = main(["run", str(EXAMPLES / "repo_risk.yaml"),
                    "--input", '{"repo_path": "/tmp/test"}'])
        assert rc == 1
        err = capsys.readouterr().err
        assert "failed" in err.lower() or "not found" in err.lower()

    def test_run_with_bad_input_json(self, capsys) -> None:
        rc = main(["run", str(EXAMPLES / "repo_risk.yaml"),
                    "--input", "not-json"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "JSON" in err

    def test_run_missing_file(self, capsys) -> None:
        rc = main(["run", "nonexistent.yaml"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "Load error" in err


class TestHelp:
    def test_no_command_shows_help(self, capsys) -> None:
        rc = main([])
        assert rc == 1

    def test_validate_help(self, capsys) -> None:
        try:
            main(["validate", "--help"])
        except SystemExit:
            pass
        out = capsys.readouterr().out
        assert "graph" in out.lower()

    def test_run_help(self, capsys) -> None:
        try:
            main(["run", "--help"])
        except SystemExit:
            pass
        out = capsys.readouterr().out
        assert "--registry" in out

    def test_diff_help(self, capsys) -> None:
        try:
            main(["diff", "--help"])
        except SystemExit:
            pass
        out = capsys.readouterr().out
        assert "old_graph" in out
