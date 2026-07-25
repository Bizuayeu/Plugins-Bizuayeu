#!/usr/bin/env python3
"""
status_cli テスト
=================

JSON 出力スキーマ:
    {
        "status": "ok",
        "metrics": {
            "raw_entries_count": <int>,
            "alias_records_total": <int>,
            "alias_records_active": <int>,
            "alias_records_archived": <int>,
            "alias_per_shard": {...},
            "unclassified_count": <int>
        }
    }
"""

import json
from pathlib import Path

import pytest

from infrastructure.repositories.entry_repository import FileEntryRepository
from interfaces import resolver_cli, status_cli
from test.test_helpers import build_raw_entry


@pytest.fixture
def plugin_root(tmp_path: Path) -> Path:
    (tmp_path / "_root.md").write_text("# root", encoding="utf-8")
    return tmp_path


def _read_stdout(capsys: pytest.CaptureFixture[str]) -> dict:  # type: ignore[type-arg]
    return json.loads(capsys.readouterr().out)


@pytest.mark.cli
class TestStatusCli:
    def test_empty_plugin_returns_zero_metrics(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = status_cli.main(["--plugin-root", str(plugin_root)])
        assert exit_code == 0
        result = _read_stdout(capsys)
        assert result["status"] == "ok"
        assert result["metrics"]["raw_entries_count"] == 0
        assert result["metrics"]["alias_records_total"] == 0
        assert result["metrics"]["unclassified_count"] == 0

    def test_counts_raw_entries(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        raw_dir = plugin_root / "inbox" / "raw-entries"
        raw_dir.mkdir(parents=True)
        repo = FileEntryRepository(raw_entries_dir=raw_dir)
        for i in range(3):
            repo.save(build_raw_entry(entry_id=f"email_20260407_14302{i}_aaaaaaaa"))

        status_cli.main(["--plugin-root", str(plugin_root)])
        result = _read_stdout(capsys)
        assert result["metrics"]["raw_entries_count"] == 3

    def test_counts_alias_records(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        for slug in ["A", "B"]:
            resolver_cli.main(
                [
                    "add",
                    "--plugin-root",
                    str(plugin_root),
                    "--kind",
                    "projects",
                    "--slug",
                    slug,
                    "--canonical",
                    slug,
                    "--target-path",
                    f"shards/projects/{slug}/_project.md",
                ]
            )
            capsys.readouterr()

        status_cli.main(["--plugin-root", str(plugin_root)])
        result = _read_stdout(capsys)
        assert result["metrics"]["alias_records_total"] == 2
        assert result["metrics"]["alias_records_active"] == 2
        assert result["metrics"]["alias_per_shard"]["projects"] == 2

    def test_counts_unclassified_dir(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        unclassified = plugin_root / "inbox" / "unclassified"
        unclassified.mkdir(parents=True)
        for i in range(2):
            (unclassified / f"x{i}.md").write_text("dummy")

        status_cli.main(["--plugin-root", str(plugin_root)])
        result = _read_stdout(capsys)
        assert result["metrics"]["unclassified_count"] == 2
