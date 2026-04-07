#!/usr/bin/env python3
"""
archive_cli テスト
==================

JSON 出力スキーマ:
    plan:
        {"status": "ok", "action": "plan", "manifest": {...}}
    execute:
        {"status": "ok", "action": "execute", "manifest": {...}, "moved": <bool>}

検証ポイント:
- plan: manifest 生成のみ（resolver 非更新、ファイル非移動）
- execute --no-move: resolver 更新のみ（ファイル移動なし）
- execute (default): resolver 更新 + ファイル移動
- 未登録案件で exit 1
- 既にアーカイブ済みで exit 1
"""

import json
from pathlib import Path

import pytest

from interfaces import archive_cli, resolver_cli


@pytest.fixture
def plugin_root(tmp_path: Path) -> Path:
    (tmp_path / "_root.md").write_text("# root", encoding="utf-8")
    return tmp_path


def _seed_project(
    plugin_root: Path,
    capsys: pytest.CaptureFixture[str],
    slug: str = "MaruMaru",
    canonical: str = "○○マンション",
) -> None:
    resolver_cli.main(
        [
            "add",
            "--plugin-root", str(plugin_root),
            "--kind", "projects",
            "--slug", slug,
            "--canonical", canonical,
            "--target-path", f"shards/projects/{slug}/_project.md",
        ]
    )
    capsys.readouterr()


def _read_stdout(capsys: pytest.CaptureFixture[str]) -> dict:  # type: ignore[type-arg]
    return json.loads(capsys.readouterr().out)


# =============================================================================
# plan
# =============================================================================


@pytest.mark.cli
class TestArchiveCliPlan:
    def test_plan_returns_manifest(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _seed_project(plugin_root, capsys)
        exit_code = archive_cli.main(
            ["plan", "--plugin-root", str(plugin_root), "--project", "MaruMaru"]
        )
        assert exit_code == 0
        result = _read_stdout(capsys)
        assert result["status"] == "ok"
        assert result["action"] == "plan"
        assert result["manifest"]["project_slug"] == "MaruMaru"

    def test_plan_does_not_modify_resolver(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _seed_project(plugin_root, capsys)
        archive_cli.main(
            ["plan", "--plugin-root", str(plugin_root), "--project", "MaruMaru"]
        )
        capsys.readouterr()
        # resolver は変更されていない
        resolver_cli.main(
            ["list", "--plugin-root", str(plugin_root)]
        )
        result = _read_stdout(capsys)
        assert result["count"] == 1  # active のまま

    def test_plan_unknown_project_fails(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as excinfo:
            archive_cli.main(
                ["plan", "--plugin-root", str(plugin_root), "--project", "Unknown"]
            )
        assert excinfo.value.code == 1


# =============================================================================
# execute
# =============================================================================


@pytest.mark.cli
class TestArchiveCliExecute:
    def test_execute_marks_archived(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _seed_project(plugin_root, capsys)
        # 移動対象ディレクトリを作成
        src_dir = plugin_root / "shards" / "projects" / "MaruMaru"
        src_dir.mkdir(parents=True)
        (src_dir / "_project.md").write_text("# project", encoding="utf-8")

        exit_code = archive_cli.main(
            ["execute", "--plugin-root", str(plugin_root), "--project", "MaruMaru"]
        )
        assert exit_code == 0
        result = _read_stdout(capsys)
        assert result["action"] == "execute"
        assert result["moved"] is True
        # 移動済み
        assert (plugin_root / "archive" / "projects" / "MaruMaru" / "_project.md").exists()
        assert not src_dir.exists()

    def test_execute_no_move_flag(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--no-move でファイル移動をスキップ（resolver 更新のみ）"""
        _seed_project(plugin_root, capsys)
        src_dir = plugin_root / "shards" / "projects" / "MaruMaru"
        src_dir.mkdir(parents=True)
        (src_dir / "_project.md").write_text("# project", encoding="utf-8")

        archive_cli.main(
            [
                "execute",
                "--plugin-root", str(plugin_root),
                "--project", "MaruMaru",
                "--no-move",
            ]
        )
        result = _read_stdout(capsys)
        assert result["moved"] is False
        # ファイルは元の場所に残る
        assert src_dir.exists()

    def test_execute_already_archived_fails(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _seed_project(plugin_root, capsys)
        src_dir = plugin_root / "shards" / "projects" / "MaruMaru"
        src_dir.mkdir(parents=True)
        (src_dir / "_project.md").write_text("# project", encoding="utf-8")

        archive_cli.main(
            ["execute", "--plugin-root", str(plugin_root), "--project", "MaruMaru"]
        )
        capsys.readouterr()

        with pytest.raises(SystemExit) as excinfo:
            archive_cli.main(
                ["execute", "--plugin-root", str(plugin_root), "--project", "MaruMaru"]
            )
        assert excinfo.value.code == 1

    def test_execute_with_reason(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _seed_project(plugin_root, capsys)
        archive_cli.main(
            [
                "execute",
                "--plugin-root", str(plugin_root),
                "--project", "MaruMaru",
                "--reason", "完工",
                "--no-move",
            ]
        )
        result = _read_stdout(capsys)
        assert result["manifest"]["reason"] == "完工"
