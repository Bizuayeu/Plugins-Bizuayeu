#!/usr/bin/env python3
"""
resolver_cli テスト
===================

サブコマンド: add / edit / remove / list / find

JSON 出力スキーマ:
- add/edit/remove: {status, action, id}
- list:           {status, count, records: [...]}
- find:           {status, record: {...}}
"""

import json
from pathlib import Path

import pytest

from interfaces import resolver_cli

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def plugin_root(tmp_path: Path) -> Path:
    (tmp_path / "_root.md").write_text("# root", encoding="utf-8")
    return tmp_path


def _read_stdout_as_json(capsys: pytest.CaptureFixture[str]) -> dict:  # type: ignore[type-arg]
    out = capsys.readouterr().out
    return json.loads(out)


# =============================================================================
# add
# =============================================================================


@pytest.mark.cli
class TestResolverCliAdd:
    def test_add_creates_record(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = resolver_cli.main(
            [
                "add",
                "--plugin-root",
                str(plugin_root),
                "--kind",
                "projects",
                "--slug",
                "MaruMaru",
                "--canonical",
                "○○マンション",
                "--target-path",
                "shards/projects/MaruMaru/_project.md",
                "--aliases",
                "○○MS,2026-003",
            ]
        )
        assert exit_code == 0
        result = _read_stdout_as_json(capsys)
        assert result["status"] == "ok"
        assert result["action"] == "add"
        assert result["id"] == "projects/MaruMaru"

    def test_add_persists_to_resolver_file(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        resolver_cli.main(
            [
                "add",
                "--plugin-root",
                str(plugin_root),
                "--kind",
                "projects",
                "--slug",
                "X",
                "--canonical",
                "X案件",
                "--target-path",
                "shards/projects/X/_project.md",
            ]
        )
        capsys.readouterr()
        assert (plugin_root / "_alias_resolver.md").exists()

    def test_add_no_aliases(self, plugin_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """--aliases 省略時は空"""
        exit_code = resolver_cli.main(
            [
                "add",
                "--plugin-root",
                str(plugin_root),
                "--kind",
                "clients",
                "--slug",
                "C",
                "--canonical",
                "C社",
                "--target-path",
                "shards/clients/C.md",
            ]
        )
        assert exit_code == 0

    def test_add_duplicate_id_fails(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        resolver_cli.main(
            [
                "add",
                "--plugin-root",
                str(plugin_root),
                "--kind",
                "projects",
                "--slug",
                "Dup",
                "--canonical",
                "Dup",
                "--target-path",
                "shards/projects/Dup/_project.md",
            ]
        )
        capsys.readouterr()
        with pytest.raises(SystemExit) as excinfo:
            resolver_cli.main(
                [
                    "add",
                    "--plugin-root",
                    str(plugin_root),
                    "--kind",
                    "projects",
                    "--slug",
                    "Dup",
                    "--canonical",
                    "Dup",
                    "--target-path",
                    "shards/projects/Dup/_project.md",
                ]
            )
        assert excinfo.value.code == 1
        result = _read_stdout_as_json(capsys)
        assert result["status"] == "error"


# =============================================================================
# edit
# =============================================================================


@pytest.mark.cli
class TestResolverCliEdit:
    def _seed(self, plugin_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
        resolver_cli.main(
            [
                "add",
                "--plugin-root",
                str(plugin_root),
                "--kind",
                "projects",
                "--slug",
                "X",
                "--canonical",
                "旧名",
                "--target-path",
                "shards/projects/X/_project.md",
                "--aliases",
                "old1",
            ]
        )
        capsys.readouterr()

    def test_edit_canonical(self, plugin_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
        self._seed(plugin_root, capsys)
        exit_code = resolver_cli.main(
            [
                "edit",
                "--plugin-root",
                str(plugin_root),
                "--id",
                "projects/X",
                "--canonical",
                "新名",
            ]
        )
        assert exit_code == 0
        result = _read_stdout_as_json(capsys)
        assert result["action"] == "edit"
        assert result["id"] == "projects/X"

    def test_edit_add_aliases(self, plugin_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
        self._seed(plugin_root, capsys)
        exit_code = resolver_cli.main(
            [
                "edit",
                "--plugin-root",
                str(plugin_root),
                "--id",
                "projects/X",
                "--add-aliases",
                "new1,new2",
            ]
        )
        assert exit_code == 0
        capsys.readouterr()

    def test_edit_unknown_id_fails(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as excinfo:
            resolver_cli.main(
                [
                    "edit",
                    "--plugin-root",
                    str(plugin_root),
                    "--id",
                    "projects/Unknown",
                    "--canonical",
                    "X",
                ]
            )
        assert excinfo.value.code == 1
        result = _read_stdout_as_json(capsys)
        assert result["status"] == "error"


# =============================================================================
# remove
# =============================================================================


@pytest.mark.cli
class TestResolverCliRemove:
    def test_remove_marks_archived(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        resolver_cli.main(
            [
                "add",
                "--plugin-root",
                str(plugin_root),
                "--kind",
                "projects",
                "--slug",
                "X",
                "--canonical",
                "X",
                "--target-path",
                "shards/projects/X/_project.md",
            ]
        )
        capsys.readouterr()
        exit_code = resolver_cli.main(
            ["remove", "--plugin-root", str(plugin_root), "--id", "projects/X"]
        )
        assert exit_code == 0
        result = _read_stdout_as_json(capsys)
        assert result["action"] == "remove"


# =============================================================================
# list
# =============================================================================


@pytest.mark.cli
class TestResolverCliList:
    def test_list_empty(self, plugin_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = resolver_cli.main(["list", "--plugin-root", str(plugin_root)])
        assert exit_code == 0
        result = _read_stdout_as_json(capsys)
        assert result["count"] == 0
        assert result["records"] == []

    def test_list_excludes_archived_by_default(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        for slug, archive in [("Active", False), ("Done", True)]:
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
            if archive:
                resolver_cli.main(
                    ["remove", "--plugin-root", str(plugin_root), "--id", f"projects/{slug}"]
                )
                capsys.readouterr()

        resolver_cli.main(["list", "--plugin-root", str(plugin_root)])
        result = _read_stdout_as_json(capsys)
        ids = [r["id"] for r in result["records"]]
        assert "projects/Active" in ids
        assert "projects/Done" not in ids

    def test_list_include_archived(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        resolver_cli.main(
            [
                "add",
                "--plugin-root",
                str(plugin_root),
                "--kind",
                "projects",
                "--slug",
                "Done",
                "--canonical",
                "Done",
                "--target-path",
                "shards/projects/Done/_project.md",
            ]
        )
        capsys.readouterr()
        resolver_cli.main(["remove", "--plugin-root", str(plugin_root), "--id", "projects/Done"])
        capsys.readouterr()
        resolver_cli.main(["list", "--plugin-root", str(plugin_root), "--include-archived"])
        result = _read_stdout_as_json(capsys)
        assert result["count"] == 1


# =============================================================================
# find
# =============================================================================


@pytest.mark.cli
class TestResolverCliFind:
    def test_find_existing(self, plugin_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
        resolver_cli.main(
            [
                "add",
                "--plugin-root",
                str(plugin_root),
                "--kind",
                "projects",
                "--slug",
                "X",
                "--canonical",
                "Xs",
                "--target-path",
                "shards/projects/X/_project.md",
            ]
        )
        capsys.readouterr()
        exit_code = resolver_cli.main(
            ["find", "--plugin-root", str(plugin_root), "--id", "projects/X"]
        )
        assert exit_code == 0
        result = _read_stdout_as_json(capsys)
        assert result["record"]["id"] == "projects/X"

    def test_find_unknown_fails(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as excinfo:
            resolver_cli.main(
                ["find", "--plugin-root", str(plugin_root), "--id", "projects/Unknown"]
            )
        assert excinfo.value.code == 1
