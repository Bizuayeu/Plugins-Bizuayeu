#!/usr/bin/env python3
"""
triage_cli テスト
=================

triage CLI の検証。

検証ポイント:
- raw-entries/ から全エントリを読み込み triage
- alias resolver のレコードからルール生成（canonical / aliases を subject パターンに）
- --no-llm: LLM フォールバックなしで unclassified を許容
- triage_logs/ への追記
- JSON 出力: status / classified / rule_match / unclassified / total
"""

import json
from pathlib import Path

import pytest

from infrastructure.repositories.entry_repository import FileEntryRepository
from interfaces import resolver_cli, triage_cli
from test.test_helpers import build_raw_entry

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def plugin_root(tmp_path: Path) -> Path:
    (tmp_path / "_root.md").write_text("# root", encoding="utf-8")
    return tmp_path


def _add_resolver_record(
    plugin_root: Path,
    capsys: pytest.CaptureFixture[str],
    *,
    kind: str,
    slug: str,
    canonical: str,
    aliases: str = "",
) -> None:
    resolver_cli.main(
        [
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
            *(["--aliases", aliases] if aliases else []),
        ]
    )
    capsys.readouterr()


def _seed_raw_entry(plugin_root: Path, **overrides) -> None:  # type: ignore[no-untyped-def]
    raw_dir = plugin_root / "inbox" / "raw-entries"
    raw_dir.mkdir(parents=True, exist_ok=True)
    repo = FileEntryRepository(raw_entries_dir=raw_dir)
    repo.save(build_raw_entry(**overrides))


def _read_stdout(capsys: pytest.CaptureFixture[str]) -> dict:  # type: ignore[type-arg]
    return json.loads(capsys.readouterr().out)


# =============================================================================
# 正常系
# =============================================================================


@pytest.mark.cli
class TestTriageCli:
    def test_no_entries_returns_zero_total(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (plugin_root / "inbox" / "raw-entries").mkdir(parents=True)
        exit_code = triage_cli.main(["--plugin-root", str(plugin_root), "--no-llm"])
        assert exit_code == 0
        result = _read_stdout(capsys)
        assert result["status"] == "ok"
        assert result["total"] == 0

    def test_rule_match_via_canonical(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """resolver の canonical が subject にあれば rule_match"""
        _add_resolver_record(
            plugin_root,
            capsys,
            kind="projects",
            slug="MaruMaru",
            canonical="MaruMaruMansion",
        )
        _seed_raw_entry(
            plugin_root,
            entry_id="email_20260407_143022_aaaaaaaa",
            subject="MaruMaruMansion ventilation",
        )

        exit_code = triage_cli.main(["--plugin-root", str(plugin_root), "--no-llm"])
        assert exit_code == 0
        result = _read_stdout(capsys)
        assert result["rule_match"] == 1
        assert result["unclassified"] == 0

    def test_rule_match_via_alias(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _add_resolver_record(
            plugin_root,
            capsys,
            kind="projects",
            slug="P1",
            canonical="ProjectOne",
            aliases="P1,proj-001",
        )
        _seed_raw_entry(
            plugin_root,
            entry_id="email_20260407_143022_bbbbbbbb",
            subject="proj-001 update",
        )

        triage_cli.main(["--plugin-root", str(plugin_root), "--no-llm"])
        result = _read_stdout(capsys)
        assert result["rule_match"] == 1

    def test_unclassified_when_no_rule_matches_and_no_llm(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _seed_raw_entry(
            plugin_root,
            entry_id="email_20260407_143022_cccccccc",
            subject="random unrelated subject",
        )
        triage_cli.main(["--plugin-root", str(plugin_root), "--no-llm"])
        result = _read_stdout(capsys)
        assert result["unclassified"] == 1
        assert result["rule_match"] == 0

    def test_writes_triage_log(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _add_resolver_record(
            plugin_root,
            capsys,
            kind="projects",
            slug="X",
            canonical="Xproject",
        )
        _seed_raw_entry(
            plugin_root,
            entry_id="email_20260407_143022_dddddddd",
            subject="Xproject update",
        )
        triage_cli.main(["--plugin-root", str(plugin_root), "--no-llm"])
        capsys.readouterr()
        log_files = list((plugin_root / "triage_logs").glob("_triage_log_*.json"))
        assert len(log_files) >= 1

    def test_mixed_results(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _add_resolver_record(
            plugin_root,
            capsys,
            kind="projects",
            slug="A",
            canonical="Alpha",
        )
        _seed_raw_entry(
            plugin_root,
            entry_id="email_20260407_143022_eeeeeeee",
            subject="Alpha kickoff",
        )
        _seed_raw_entry(
            plugin_root,
            entry_id="email_20260407_143023_ffffffff",
            subject="Beta status",
        )

        triage_cli.main(["--plugin-root", str(plugin_root), "--no-llm"])
        result = _read_stdout(capsys)
        assert result["total"] == 2
        assert result["rule_match"] == 1
        assert result["unclassified"] == 1


# =============================================================================
# エラー
# =============================================================================


@pytest.mark.cli
class TestTriageCliErrors:
    def test_missing_raw_entries_dir(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """raw-entries/ がなくても 0 件として正常終了"""
        exit_code = triage_cli.main(["--plugin-root", str(plugin_root), "--no-llm"])
        assert exit_code == 0
        result = _read_stdout(capsys)
        assert result["total"] == 0


# =============================================================================
# LLM フォールバック経路（subprocess を mock）
# =============================================================================


@pytest.mark.cli
class TestTriageCliLLMPath:
    def test_llm_fallback_via_mock(
        self,
        plugin_root: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """ClaudeCliTriageClient.classify を mock して LLM 経路を検証"""
        from unittest.mock import patch

        from infrastructure.llm.claude_cli_client import ClaudeCliTriageClient

        _seed_raw_entry(
            plugin_root,
            entry_id="email_20260407_143022_aaaaaaaa",
            subject="random subject",
        )

        with patch.object(ClaudeCliTriageClient, "classify", return_value="vendors"):
            exit_code = triage_cli.main(["--plugin-root", str(plugin_root)])

        assert exit_code == 0
        result = _read_stdout(capsys)
        assert result["llm_fallback"] == 1
        assert result["unclassified"] == 0
        assert result["rule_match"] == 0

    def test_llm_failure_returns_error(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """LLM 例外で exit 1"""
        from unittest.mock import patch

        from domain.exceptions import TriageError
        from infrastructure.llm.claude_cli_client import ClaudeCliTriageClient

        _seed_raw_entry(
            plugin_root,
            entry_id="email_20260407_143022_bbbbbbbb",
            subject="needs LLM",
        )

        with patch.object(
            ClaudeCliTriageClient, "classify", side_effect=TriageError("simulated")
        ):
            with pytest.raises(SystemExit) as excinfo:
                triage_cli.main(["--plugin-root", str(plugin_root)])
            assert excinfo.value.code == 1
        result = _read_stdout(capsys)
        assert result["status"] == "error"

    def test_regex_special_chars_in_canonical(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """canonical/aliases は re.escape されるので regex メタ文字も安全（Markdown 制約のため [ ] は不可）"""
        _add_resolver_record(
            plugin_root,
            capsys,
            kind="projects",
            slug="X",
            canonical="Proj.X+",
        )
        _seed_raw_entry(
            plugin_root,
            entry_id="email_20260407_143022_cccccccc",
            subject="Proj.X+ subject",
        )
        exit_code = triage_cli.main(["--plugin-root", str(plugin_root), "--no-llm"])
        assert exit_code == 0
        result = _read_stdout(capsys)
        assert result["rule_match"] == 1

    def test_skips_empty_alias_string(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """空の canonical/aliases は無視される（pattern 生成しない）"""
        # canonical は必須なので、aliases に空要素を混ぜるシナリオを構築
        # （resolver_cli は empty alias を split で除外するので、ここでは正常系の確認）
        _add_resolver_record(
            plugin_root,
            capsys,
            kind="projects",
            slug="X",
            canonical="ProjX",
        )
        _seed_raw_entry(
            plugin_root,
            entry_id="email_20260407_143022_dddddddd",
            subject="random",
        )
        exit_code = triage_cli.main(["--plugin-root", str(plugin_root), "--no-llm"])
        assert exit_code == 0
