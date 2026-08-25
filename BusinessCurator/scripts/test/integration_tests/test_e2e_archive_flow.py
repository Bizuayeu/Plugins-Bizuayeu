#!/usr/bin/env python3
"""
E2E: Archive Flow
=================

案件登録 → ファイル準備 → archive plan → archive execute → 結果検証 の通しシナリオ。

シナリオ:
1. plugin_root を準備
2. project を resolver に add
3. shards/projects/<slug>/_project.md を手動配置（実プロジェクト準備）
4. archive plan で manifest 確認（副作用なし）
5. archive execute でファイル移動 + resolver 更新
6. 結果検証:
   - shards/projects/<slug>/ が消えている
   - archive/projects/<slug>/_project.md が存在
   - resolver で archived = True
   - target_path が archive/ に変わっている
7. 二重 execute で fail
8. リネーム後の resolver list で確認
"""

import json
from pathlib import Path

import pytest

from interfaces import archive_cli, resolver_cli, status_cli


@pytest.fixture
def plugin_root(tmp_path: Path) -> Path:
    (tmp_path / "_root.md").write_text("# root", encoding="utf-8")
    return tmp_path


def _capture_json(capsys: pytest.CaptureFixture[str]) -> dict:  # type: ignore[type-arg]
    return json.loads(capsys.readouterr().out)


def _setup_project(
    plugin_root: Path,
    capsys: pytest.CaptureFixture[str],
    slug: str,
    canonical: str,
) -> None:
    """resolver に add + shards/projects/<slug>/_project.md を配置"""
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
            canonical,
            "--target-path",
            f"shards/projects/{slug}/_project.md",
        ]
    )
    capsys.readouterr()
    src_dir = plugin_root / "shards" / "projects" / slug
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "_project.md").write_text(
        f"# {canonical}\n\n- ステータス: active\n", encoding="utf-8"
    )
    (src_dir / "topic-design.md").write_text("# 設計判断\n", encoding="utf-8")


# =============================================================================
# 通常の archive 完工フロー
# =============================================================================


@pytest.mark.integration
class TestArchiveFlowHappyPathE2E:
    def test_full_archive_flow(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # ----- Step 1: project を準備 -----
        _setup_project(plugin_root, capsys, "MaruMaru", "○○マンション")

        src_dir = plugin_root / "shards" / "projects" / "MaruMaru"
        dst_dir = plugin_root / "archive" / "projects" / "MaruMaru"
        assert src_dir.exists()
        assert not dst_dir.exists()

        # ----- Step 2: archive plan (副作用なし) -----
        archive_cli.main(
            [
                "plan",
                "--plugin-root",
                str(plugin_root),
                "--project",
                "MaruMaru",
                "--reason",
                "completed",
            ]
        )
        result = _capture_json(capsys)
        assert result["action"] == "plan"
        assert result["manifest"]["project_slug"] == "MaruMaru"
        assert result["manifest"]["project_canonical"] == "○○マンション"
        assert result["manifest"]["reason"] == "completed"
        # plan は副作用なし: ファイルも resolver も変わらない
        assert src_dir.exists()
        assert not dst_dir.exists()

        # ----- Step 3: status で archive 前を確認 -----
        status_cli.main(["--plugin-root", str(plugin_root)])
        result = _capture_json(capsys)
        assert result["metrics"]["alias_records_active"] == 1
        assert result["metrics"]["alias_records_archived"] == 0

        # ----- Step 4: archive execute -----
        archive_cli.main(
            [
                "execute",
                "--plugin-root",
                str(plugin_root),
                "--project",
                "MaruMaru",
                "--reason",
                "completed",
            ]
        )
        result = _capture_json(capsys)
        assert result["action"] == "execute"
        assert result["moved"] is True
        assert result["manifest"]["destination_path"] == "archive/projects/MaruMaru"

        # ----- Step 5: ファイルシステム検証 -----
        assert not src_dir.exists(), "source dir should be moved away"
        assert dst_dir.exists()
        assert (dst_dir / "_project.md").exists()
        assert (dst_dir / "topic-design.md").exists()

        # ----- Step 6: resolver で archive_status 確認 -----
        status_cli.main(["--plugin-root", str(plugin_root)])
        result = _capture_json(capsys)
        assert result["metrics"]["alias_records_active"] == 0
        assert result["metrics"]["alias_records_completed"] == 1

        # find で target_path が archive/ に切り替わっていることを確認
        resolver_cli.main(
            ["find", "--plugin-root", str(plugin_root), "--id", "projects/MaruMaru"]
        )
        result = _capture_json(capsys)
        assert result["record"]["archive_status"] == "completed"
        assert "archive/projects/MaruMaru" in result["record"]["target_path"]

        # ----- Step 7: 二重 archive で fail -----
        with pytest.raises(SystemExit) as excinfo:
            archive_cli.main(
                [
                    "execute",
                    "--plugin-root",
                    str(plugin_root),
                    "--project",
                    "MaruMaru",
                ]
            )
        assert excinfo.value.code == 1
        result = _capture_json(capsys)
        assert result["status"] == "error"
        assert "already archived" in result["error"]


# =============================================================================
# --no-move フロー（resolver 更新のみ）
# =============================================================================


@pytest.mark.integration
class TestArchiveNoMoveE2E:
    def test_no_move_keeps_files_in_place(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _setup_project(plugin_root, capsys, "X", "X案件")

        src_dir = plugin_root / "shards" / "projects" / "X"

        archive_cli.main(
            [
                "execute",
                "--plugin-root",
                str(plugin_root),
                "--project",
                "X",
                "--no-move",
            ]
        )
        result = _capture_json(capsys)
        assert result["moved"] is False

        # ファイルは元の場所
        assert src_dir.exists()
        assert (src_dir / "_project.md").exists()

        # resolver の archive_status は completed
        resolver_cli.main(
            ["find", "--plugin-root", str(plugin_root), "--id", "projects/X"]
        )
        result = _capture_json(capsys)
        assert result["record"]["archive_status"] == "completed"


# =============================================================================
# 移動先既存エラー
# =============================================================================


@pytest.mark.integration
class TestArchiveDestinationExistsE2E:
    def test_destination_exists_fails_with_manifest_in_details(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _setup_project(plugin_root, capsys, "Y", "Y案件")
        # 移動先を事前に作成しておく → 衝突
        dst_dir = plugin_root / "archive" / "projects" / "Y"
        dst_dir.mkdir(parents=True)
        (dst_dir / "stale.md").write_text("preexisting", encoding="utf-8")

        with pytest.raises(SystemExit) as excinfo:
            archive_cli.main(
                [
                    "execute",
                    "--plugin-root",
                    str(plugin_root),
                    "--project",
                    "Y",
                ]
            )
        assert excinfo.value.code == 1
        result = _capture_json(capsys)
        assert result["status"] == "error"
        assert "destination already exists" in result["error"]
        # マニフェストは details に含まれる
        assert "manifest" in result.get("details", {})


# =============================================================================
# 複数案件の一括 archive
# =============================================================================


@pytest.mark.integration
class TestMultiProjectArchiveE2E:
    def test_archive_two_projects_independently(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _setup_project(plugin_root, capsys, "P1", "P1")
        _setup_project(plugin_root, capsys, "P2", "P2")

        for slug in ["P1", "P2"]:
            archive_cli.main(
                [
                    "execute",
                    "--plugin-root",
                    str(plugin_root),
                    "--project",
                    slug,
                ]
            )
            capsys.readouterr()

        status_cli.main(["--plugin-root", str(plugin_root)])
        result = _capture_json(capsys)
        assert result["metrics"]["alias_records_archived"] == 2
        assert result["metrics"]["alias_records_active"] == 0

        # archive/projects/ 配下に両方の slug が存在
        assert (plugin_root / "archive" / "projects" / "P1").exists()
        assert (plugin_root / "archive" / "projects" / "P2").exists()
