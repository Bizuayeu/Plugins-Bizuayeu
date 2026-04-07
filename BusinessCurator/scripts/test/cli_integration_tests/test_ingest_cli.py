#!/usr/bin/env python3
"""
ingest_cli テスト
=================

Phase 4.1: in-process + subprocess の二段テスト戦略

- in-process: argparse Namespace 直接呼び出し（高速、capsys でキャプチャ）
- subprocess (sanity): 実際に python -m interfaces.ingest_cli を1回起動

検証ポイント:
- ingest --source <path> --plugin-root <path> → 実 .eml をパース → raw-entries/ に保存
- JSON 出力: status / saved / skipped / failed / total
- 同じソース2回 → saved=N, skipped=N (冪等性)
- ソース不存在 → exit 1, status=error
"""

import json
import shutil
from pathlib import Path

import pytest

from interfaces import ingest_cli

from .cli_runner import CLIRunner

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "emails"

# =============================================================================
# Helpers
# =============================================================================


@pytest.fixture
def plugin_root(tmp_path: Path) -> Path:
    """テスト用 plugin_root を準備"""
    (tmp_path / "_root.md").write_text("# root", encoding="utf-8")
    (tmp_path / "inbox" / "raw-entries").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def sample_eml_path(plugin_root: Path) -> Path:
    """fixtures から .eml をコピーして plugin_root に配置"""
    src = FIXTURE_DIR / "sample_simple.eml"
    dst = plugin_root / "data" / "sample_simple.eml"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)
    return dst


# =============================================================================
# in-process: 正常系
# =============================================================================


@pytest.mark.cli
class TestIngestCliInProcess:
    def test_eml_source_saves_one_entry(
        self, plugin_root: Path, sample_eml_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = ingest_cli.main(
            ["--source", str(sample_eml_path), "--plugin-root", str(plugin_root)]
        )
        assert exit_code == 0
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "ok"
        assert result["saved"] == 1
        assert result["skipped"] == 0

    def test_creates_md_file_in_raw_entries(
        self, plugin_root: Path, sample_eml_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ingest_cli.main(
            ["--source", str(sample_eml_path), "--plugin-root", str(plugin_root)]
        )
        capsys.readouterr()
        md_files = list((plugin_root / "inbox" / "raw-entries").glob("*.md"))
        assert len(md_files) == 1

    def test_idempotent_re_run(
        self, plugin_root: Path, sample_eml_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """2回目は skipped=1"""
        ingest_cli.main(
            ["--source", str(sample_eml_path), "--plugin-root", str(plugin_root)]
        )
        capsys.readouterr()
        ingest_cli.main(
            ["--source", str(sample_eml_path), "--plugin-root", str(plugin_root)]
        )
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["saved"] == 0
        assert result["skipped"] == 1

    def test_mbox_source(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """5通入り mbox を ingest"""
        src = FIXTURE_DIR / "sample_5_messages.mbox"
        dst = plugin_root / "data" / "sample.mbox"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)

        exit_code = ingest_cli.main(
            ["--source", str(dst), "--plugin-root", str(plugin_root)]
        )
        assert exit_code == 0
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["saved"] == 5

    def test_auto_detects_format(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """拡張子なしファイルでもシグネチャ検出 → ingest 成功"""
        src = FIXTURE_DIR / "sample_simple.eml"
        dst = plugin_root / "data" / "no_extension"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)

        exit_code = ingest_cli.main(
            ["--source", str(dst), "--plugin-root", str(plugin_root)]
        )
        assert exit_code == 0


# =============================================================================
# in-process: エラー系
# =============================================================================


@pytest.mark.cli
class TestIngestCliErrors:
    def test_missing_source_returns_exit_1(
        self, plugin_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """存在しない source → exit 1, status=error"""
        with pytest.raises(SystemExit) as excinfo:
            ingest_cli.main(
                [
                    "--source",
                    str(plugin_root / "nope.eml"),
                    "--plugin-root",
                    str(plugin_root),
                ]
            )
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "error"

    def test_missing_plugin_root_marker(
        self, tmp_path: Path, sample_eml_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """plugin_root に _root.md がなくても、--plugin-root 明示なら raw-entries 作成"""
        # plugin_root 未準備の tmp_path を直接指定
        bare = tmp_path / "bare"
        bare.mkdir()
        src = bare / "x.eml"
        shutil.copy(FIXTURE_DIR / "sample_simple.eml", src)
        exit_code = ingest_cli.main(
            ["--source", str(src), "--plugin-root", str(bare)]
        )
        # 明示指定なので成功する（マーカー不要）
        assert exit_code == 0


# =============================================================================
# subprocess (sanity)
# =============================================================================


@pytest.mark.cli
class TestIngestCliSubprocess:
    """subprocess 経由で1度だけ実行（in-process と subprocess 両対応の sanity check）"""

    def test_subprocess_invocation_succeeds(self, plugin_root: Path) -> None:
        src = FIXTURE_DIR / "sample_simple.eml"
        dst = plugin_root / "data" / "x.eml"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)

        runner = CLIRunner()
        result = runner.run_module(
            "interfaces.ingest_cli",
            source=str(dst),
            plugin_root=str(plugin_root),
        )
        result.assert_success()
        assert result.json_output is not None
        assert result.json_output["status"] == "ok"
