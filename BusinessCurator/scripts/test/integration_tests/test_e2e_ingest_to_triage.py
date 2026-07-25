#!/usr/bin/env python3
"""
E2E: Ingest → Triage → Status
==============================

メール取り込みから振り分け、ステータス確認までの通しシナリオ。

シナリオ:
1. plugin_root を準備
2. manager 系 CLI で 3 エンティティ登録 (projects/MaruMaru, clients/Shikaku, vendors/Sankaku)
3. 5通入り mbox を ingest → raw-entries に5件
4. triage --no-llm を実行 → ルールマッチ4件 + unclassified 1件
5. status で metrics を確認
6. triage_logs/_triage_log_*.json が作られていることを確認
7. 2回目の ingest で skip されることを確認 (冪等性)
"""

import json
import shutil
from pathlib import Path

import pytest

from interfaces import ingest_cli, resolver_cli, status_cli, triage_cli

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "emails"


@pytest.fixture
def plugin_root(tmp_path: Path) -> Path:
    (tmp_path / "_root.md").write_text("# root", encoding="utf-8")
    return tmp_path


def _capture_json(capsys: pytest.CaptureFixture[str]) -> dict:  # type: ignore[type-arg]
    return json.loads(capsys.readouterr().out)


def _add_entity(
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
# Full pipeline
# =============================================================================


@pytest.mark.integration
class TestIngestToTriagePipelineE2E:
    def test_full_pipeline(self, plugin_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
        # ----- Step 1: マスタデータ登録 -----
        _add_entity(plugin_root, capsys, "projects", "MaruMaru", "MaruMaruMansion")
        _add_entity(
            plugin_root, capsys, "clients", "Shikaku", "ShikakuFudosan", "shikaku.example.jp"
        )
        _add_entity(
            plugin_root, capsys, "vendors", "Sankaku", "SankakuSetsubi", "sankaku.example.jp"
        )

        # ----- Step 2: ingest -----
        src = FIXTURE_DIR / "sample_mixed_meguru.mbox"
        dst = plugin_root / "data" / "sample.mbox"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)

        exit_code = ingest_cli.main(["--source", str(dst), "--plugin-root", str(plugin_root)])
        assert exit_code == 0
        result = _capture_json(capsys)
        assert result["saved"] == 5
        assert result["total"] == 5

        # raw-entries/ に5件
        raw_files = list((plugin_root / "inbox" / "raw-entries").glob("*.md"))
        assert len(raw_files) == 5

        # ----- Step 3: triage --no-llm -----
        exit_code = triage_cli.main(["--plugin-root", str(plugin_root), "--no-llm"])
        assert exit_code == 0
        result = _capture_json(capsys)
        assert result["total"] == 5
        # MaruMaruMansion x2 + ShikakuFudosan + SankakuSetsubi = 4 件 rule_match
        # unrelated = 1 件 unclassified
        assert result["rule_match"] == 4
        assert result["unclassified"] == 1
        assert result["llm_fallback"] == 0

        # ----- Step 4: triage_logs に追記 -----
        log_files = list((plugin_root / "triage_logs").glob("_triage_log_*.json"))
        assert len(log_files) >= 1
        log_data = json.loads(log_files[0].read_text(encoding="utf-8"))
        assert len(log_data) == 5
        # 各エントリに decision がある
        for entry in log_data:
            assert "timestamp" in entry
            assert "decision" in entry
            assert "llm_invoked" in entry

        # ----- Step 5: status で metrics 確認 -----
        status_cli.main(["--plugin-root", str(plugin_root)])
        result = _capture_json(capsys)
        m = result["metrics"]
        assert m["raw_entries_count"] == 5
        assert m["alias_records_total"] == 3
        assert m["alias_records_active"] == 3

        # ----- Step 6: 2回目 ingest で冪等性確認 -----
        ingest_cli.main(["--source", str(dst), "--plugin-root", str(plugin_root)])
        result = _capture_json(capsys)
        assert result["saved"] == 0
        assert result["skipped"] == 5

        # raw-entries/ は依然 5 件
        raw_files = list((plugin_root / "inbox" / "raw-entries").glob("*.md"))
        assert len(raw_files) == 5


# =============================================================================
# triage 後の rule 更新シナリオ
# =============================================================================


@pytest.mark.integration
class TestTriageRuleUpdateE2E:
    """unclassified エントリに対し alias を追加して再 triage で rule_match に変わる"""

    def test_alias_addition_recovers_unclassified(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # 1件だけ ingest（unclassified になるシンプルなケース）
        _add_entity(plugin_root, capsys, "projects", "X", "ProjectX")
        # raw-entries に1件直接書き込み（subject に "ProjectY" を含む）
        from infrastructure.repositories.entry_repository import FileEntryRepository
        from test.test_helpers import build_raw_entry

        raw_dir = plugin_root / "inbox" / "raw-entries"
        raw_dir.mkdir(parents=True)
        repo = FileEntryRepository(raw_entries_dir=raw_dir)
        repo.save(
            build_raw_entry(
                entry_id="email_20260407_143022_aaaaaaaa",
                subject="ProjectY launch",
            )
        )

        # 1回目の triage: rule_match 0, unclassified 1
        triage_cli.main(["--plugin-root", str(plugin_root), "--no-llm"])
        result = _capture_json(capsys)
        assert result["rule_match"] == 0
        assert result["unclassified"] == 1

        # alias を追加 (ProjectY → projects/X)
        resolver_cli.main(
            [
                "edit",
                "--plugin-root",
                str(plugin_root),
                "--id",
                "projects/X",
                "--add-aliases",
                "ProjectY",
            ]
        )
        capsys.readouterr()

        # 2回目の triage: rule_match 1, unclassified 0
        triage_cli.main(["--plugin-root", str(plugin_root), "--no-llm"])
        result = _capture_json(capsys)
        assert result["rule_match"] == 1
        assert result["unclassified"] == 0


# =============================================================================
# Empty plugin での通しシナリオ
# =============================================================================


@pytest.mark.integration
class TestEmptyPluginE2E:
    """マスタなし・エントリなしでも全 CLI が落ちずに動く"""

    def test_empty_plugin_all_cli_succeed(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # status
        status_cli.main(["--plugin-root", str(plugin_root)])
        s = _capture_json(capsys)
        assert s["metrics"]["raw_entries_count"] == 0

        # triage (raw-entries なし)
        triage_cli.main(["--plugin-root", str(plugin_root), "--no-llm"])
        t = _capture_json(capsys)
        assert t["total"] == 0

        # list (resolver 空)
        resolver_cli.main(["list", "--plugin-root", str(plugin_root)])
        r = _capture_json(capsys)
        assert r["count"] == 0
