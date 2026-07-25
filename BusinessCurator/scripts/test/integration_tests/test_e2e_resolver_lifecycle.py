#!/usr/bin/env python3
"""
E2E: Resolver Lifecycle
=======================

resolver の add → edit → remove → list の通しシナリオ。
全層（CLI → application → infrastructure → domain）が連結して動くことを検証。

シナリオ:
1. 空の plugin_root を準備
2. 4 シャードに各1件 add（合計4件）
3. status で alias_records_total = 4 を確認
4. 1件 edit（aliases 追加）
5. find で更新内容を確認
6. 1件 remove（archived フラグ）
7. list (デフォルト) で 3 件、--include-archived で 4 件
8. _alias_resolver.md ファイルを直接読み、md フォーマットを検証
"""

import json
from pathlib import Path

import pytest

from interfaces import resolver_cli, status_cli


@pytest.fixture
def plugin_root(tmp_path: Path) -> Path:
    (tmp_path / "_root.md").write_text("# root", encoding="utf-8")
    return tmp_path


def _capture_json(capsys: pytest.CaptureFixture[str]) -> dict:  # type: ignore[type-arg]
    return json.loads(capsys.readouterr().out)


def _add(
    plugin_root: Path,
    capsys: pytest.CaptureFixture[str],
    kind: str,
    slug: str,
    canonical: str,
    aliases: str = "",
) -> None:
    args = [
        "add",
        "--plugin-root",
        str(plugin_root),
        "--kind",
        kind,
        "--slug",
        slug,
        "--canonical",
        canonical,
        "--target-path",
        f"shards/{kind}/{slug}/_project.md",
    ]
    if aliases:
        args.extend(["--aliases", aliases])
    resolver_cli.main(args)
    capsys.readouterr()


# =============================================================================
# E2E lifecycle
# =============================================================================


@pytest.mark.integration
class TestResolverLifecycleE2E:
    def test_full_lifecycle(self, plugin_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
        # ----- Step 1: 4 entities を add -----
        _add(plugin_root, capsys, "projects", "MaruMaru", "○○マンション", "MM,2026-003")
        _add(plugin_root, capsys, "clients", "Shikaku", "□□不動産", "shikaku.co.jp")
        _add(plugin_root, capsys, "vendors", "Sankaku", "△△設備", "sankaku.jp")
        _add(plugin_root, capsys, "knowledge", "houki", "法規", "排煙告示,建基法")

        # ----- Step 2: status で 4 件を確認 -----
        status_cli.main(["--plugin-root", str(plugin_root)])
        result = _capture_json(capsys)
        assert result["metrics"]["alias_records_total"] == 4
        assert result["metrics"]["alias_records_active"] == 4
        assert result["metrics"]["alias_records_archived"] == 0
        assert result["metrics"]["alias_per_shard"] == {
            "projects": 1,
            "clients": 1,
            "vendors": 1,
            "knowledge": 1,
        }

        # ----- Step 3: 1件 edit (aliases 追加) -----
        resolver_cli.main(
            [
                "edit",
                "--plugin-root",
                str(plugin_root),
                "--id",
                "projects/MaruMaru",
                "--add-aliases",
                "○○MS,maru",
            ]
        )
        capsys.readouterr()

        # ----- Step 4: find で更新確認 -----
        resolver_cli.main(["find", "--plugin-root", str(plugin_root), "--id", "projects/MaruMaru"])
        result = _capture_json(capsys)
        aliases = set(result["record"]["aliases"])
        assert "MM" in aliases
        assert "2026-003" in aliases
        assert "○○MS" in aliases
        assert "maru" in aliases

        # ----- Step 5: 1件 remove -----
        resolver_cli.main(["remove", "--plugin-root", str(plugin_root), "--id", "vendors/Sankaku"])
        capsys.readouterr()

        # ----- Step 6a: list (デフォルト = active のみ) -----
        resolver_cli.main(["list", "--plugin-root", str(plugin_root)])
        result = _capture_json(capsys)
        assert result["count"] == 3
        active_ids = {r["id"] for r in result["records"]}
        assert "vendors/Sankaku" not in active_ids
        assert "projects/MaruMaru" in active_ids

        # ----- Step 6b: list --include-archived -----
        resolver_cli.main(["list", "--plugin-root", str(plugin_root), "--include-archived"])
        result = _capture_json(capsys)
        assert result["count"] == 4

        # ----- Step 7: status で archived = 1 を確認 -----
        status_cli.main(["--plugin-root", str(plugin_root)])
        result = _capture_json(capsys)
        assert result["metrics"]["alias_records_active"] == 3
        assert result["metrics"]["alias_records_archived"] == 1

        # ----- Step 8: _alias_resolver.md ファイルの md フォーマット検証 -----
        md_content = (plugin_root / "_alias_resolver.md").read_text(encoding="utf-8")
        assert "# Global Index" in md_content
        assert "## projects/" in md_content
        assert "## clients/" in md_content
        assert "## vendors/" in md_content
        assert "## knowledge/" in md_content
        assert "## archive/" in md_content  # Sankaku が移動
        assert "○○マンション" in md_content
        assert "○○MS" in md_content


# =============================================================================
# E2E shard filter
# =============================================================================


@pytest.mark.integration
class TestResolverShardFilterE2E:
    def test_list_with_shard_filter(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """list --shard <kind> でシャード絞り込みが機能"""
        for slug in ["P1", "P2", "P3"]:
            _add(plugin_root, capsys, "projects", slug, slug)
        for slug in ["C1", "C2"]:
            _add(plugin_root, capsys, "clients", slug, slug)

        resolver_cli.main(["list", "--plugin-root", str(plugin_root), "--shard", "projects"])
        result = _capture_json(capsys)
        assert result["count"] == 3
        assert all(r["shard"] == "projects" for r in result["records"])

        resolver_cli.main(["list", "--plugin-root", str(plugin_root), "--shard", "clients"])
        result = _capture_json(capsys)
        assert result["count"] == 2


# =============================================================================
# E2E duplicate detection
# =============================================================================


@pytest.mark.integration
class TestResolverDuplicateE2E:
    def test_duplicate_add_after_remove_still_fails(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """論理削除でも id 衝突は防ぐ"""
        _add(plugin_root, capsys, "projects", "X", "X")
        resolver_cli.main(["remove", "--plugin-root", str(plugin_root), "--id", "projects/X"])
        capsys.readouterr()

        with pytest.raises(SystemExit) as excinfo:
            _add(plugin_root, capsys, "projects", "X", "X (再登録)")
        assert excinfo.value.code == 1
        result = _capture_json(capsys)
        assert result["status"] == "error"
        assert "duplicate" in result["error"].lower()
