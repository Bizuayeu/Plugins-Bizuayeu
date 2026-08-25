#!/usr/bin/env python3
"""
infrastructure/llm/claude_cli_client.py テスト
================================================

ClaudeCliTriageClient の subprocess 経由 LLM 呼び出し検証。

設計方針:
- メモリ「APIキーよりサブスク前提」: claude -p subprocess 経由
- 実 subprocess は CI で動かないため、unittest.mock.patch でスタブ化
- I/F 契約のみ検証: 正常系（4 シャードのいずれかを返す）, 異常系（タイムアウト/空応答/不正応答）
"""

from unittest.mock import MagicMock, patch

import pytest

from infrastructure.llm.claude_cli_client import ClaudeCliTriageClient
from test.test_helpers import build_raw_entry

# =============================================================================
# 正常系
# =============================================================================


class TestClaudeCliTriageClientHappyPath:
    @pytest.mark.unit
    def test_returns_projects_when_response_is_projects(self) -> None:
        client = ClaudeCliTriageClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="projects\n", stderr=""
            )
            result = client.classify(build_raw_entry())
        assert result == "projects"

    @pytest.mark.unit
    def test_returns_clients(self) -> None:
        client = ClaudeCliTriageClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="clients", stderr="")
            result = client.classify(build_raw_entry())
        assert result == "clients"

    @pytest.mark.unit
    def test_returns_vendors(self) -> None:
        client = ClaudeCliTriageClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="vendors", stderr="")
            result = client.classify(build_raw_entry())
        assert result == "vendors"

    @pytest.mark.unit
    def test_returns_knowledge(self) -> None:
        client = ClaudeCliTriageClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="knowledge", stderr=""
            )
            result = client.classify(build_raw_entry())
        assert result == "knowledge"

    @pytest.mark.unit
    def test_uppercase_response_normalized(self) -> None:
        """大文字小文字を区別しない"""
        client = ClaudeCliTriageClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="PROJECTS", stderr=""
            )
            result = client.classify(build_raw_entry())
        assert result == "projects"

    @pytest.mark.unit
    def test_response_with_extra_whitespace_trimmed(self) -> None:
        client = ClaudeCliTriageClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="  projects  \n\n", stderr=""
            )
            result = client.classify(build_raw_entry())
        assert result == "projects"


# =============================================================================
# subprocess 呼び出し契約
# =============================================================================


class TestClaudeCliInvocation:
    @pytest.mark.unit
    def test_calls_claude_p_with_prompt(self) -> None:
        """subprocess.run が claude -p ... の形で呼ばれる"""
        client = ClaudeCliTriageClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="knowledge", stderr=""
            )
            client.classify(build_raw_entry(subject="排煙設備"))
        assert mock_run.called
        args, _kwargs = mock_run.call_args
        cmd = args[0]
        assert cmd[0] == "claude"
        assert "-p" in cmd

    @pytest.mark.unit
    def test_prompt_includes_entry_subject(self) -> None:
        """プロンプトに subject が含まれる"""
        client = ClaudeCliTriageClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="projects", stderr=""
            )
            client.classify(build_raw_entry(subject="○○マンション排煙"))
        cmd = mock_run.call_args[0][0]
        prompt = cmd[2]
        assert "○○マンション排煙" in prompt

    @pytest.mark.unit
    def test_uses_text_mode(self) -> None:
        """capture_output=True, text=True"""
        client = ClaudeCliTriageClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="knowledge", stderr=""
            )
            client.classify(build_raw_entry())
        kwargs = mock_run.call_args[1]
        assert kwargs.get("capture_output") is True
        assert kwargs.get("text") is True


# =============================================================================
# 異常系
# =============================================================================


class TestClaudeCliErrors:
    @pytest.mark.unit
    def test_nonzero_returncode_raises(self) -> None:
        from domain.exceptions import TriageError

        client = ClaudeCliTriageClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            with pytest.raises(TriageError, match="claude.*failed"):
                client.classify(build_raw_entry())

    @pytest.mark.unit
    def test_empty_response_raises(self) -> None:
        from domain.exceptions import TriageError

        client = ClaudeCliTriageClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            with pytest.raises(TriageError, match="empty"):
                client.classify(build_raw_entry())

    @pytest.mark.unit
    def test_invalid_shard_raises(self) -> None:
        from domain.exceptions import TriageError

        client = ClaudeCliTriageClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="garbage", stderr="")
            with pytest.raises(TriageError, match="invalid shard"):
                client.classify(build_raw_entry())

    @pytest.mark.unit
    def test_subprocess_timeout_raises(self) -> None:
        import subprocess

        from domain.exceptions import TriageError

        client = ClaudeCliTriageClient(timeout_seconds=1)
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=1)
            with pytest.raises(TriageError, match="timeout"):
                client.classify(build_raw_entry())

    @pytest.mark.unit
    def test_file_not_found_raises(self) -> None:
        """claude CLI がインストールされていない場合"""
        from domain.exceptions import TriageError

        client = ClaudeCliTriageClient()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("claude not found")
            with pytest.raises(TriageError, match="not found"):
                client.classify(build_raw_entry())
