#!/usr/bin/env python3
"""
CLI Runner Module
=================

subprocess 経由で CLI を実行するヘルパー（E2E テスト用）。
EpisodicRAG の cli_runner.py を BusinessCurator 向けに簡略化。
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CLIResult:
    """
    CLI 実行結果

    Attributes:
        exit_code: プロセス終了コード
        stdout: 標準出力
        stderr: 標準エラー
        json_output: パース済み JSON（失敗時 None）
        command: 実行コマンド
    """

    exit_code: int
    stdout: str
    stderr: str
    json_output: dict[str, Any] | None = None
    command: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.exit_code == 0

    def assert_success(self) -> None:
        assert self.exit_code == 0, (
            f"Command failed (exit {self.exit_code})\nstdout: {self.stdout}\nstderr: {self.stderr}"
        )

    def assert_failure(self, expected_code: int | None = None) -> None:
        if expected_code is not None:
            assert self.exit_code == expected_code, (
                f"Expected exit {expected_code}, got {self.exit_code}\nstdout: {self.stdout}"
            )
        else:
            assert self.exit_code != 0, (
                f"Expected non-zero exit, got {self.exit_code}\nstdout: {self.stdout}"
            )

    def assert_json_status(self, expected: str) -> None:
        assert self.json_output is not None, f"Output is not JSON: {self.stdout}"
        actual = self.json_output.get("status")
        assert actual == expected, f"Expected status '{expected}', got '{actual}'"


class CLIRunner:
    """subprocess ベースの CLI 実行ヘルパー"""

    def __init__(
        self,
        scripts_dir: Path | None = None,
        timeout: int = 30,
    ) -> None:
        self.scripts_dir = scripts_dir or self._find_scripts_dir()
        self.python = sys.executable
        self.timeout = timeout

    @staticmethod
    def _find_scripts_dir() -> Path:
        """test/cli_integration_tests/cli_runner.py から scripts/ を逆引き"""
        current = Path(__file__)
        scripts_dir = current.parent.parent.parent
        if (scripts_dir / "interfaces").exists():
            return scripts_dir
        raise RuntimeError(f"could not find scripts dir from {current}")

    def _run(self, args: list[str], cwd: Path | None = None) -> CLIResult:
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{self.scripts_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"
        env["PYTHONIOENCODING"] = "utf-8"

        try:
            proc = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                cwd=cwd or self.scripts_dir,
                env=env,
            )
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            return CLIResult(exit_code=-1, stdout="", stderr="timeout", command=args)

        json_output: dict[str, Any] | None = None
        if stdout.strip():
            try:
                json_output = json.loads(stdout.strip())
            except json.JSONDecodeError:
                json_output = None

        return CLIResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            json_output=json_output,
            command=args,
        )

    def _build_module_args(
        self, module: str, *args: str, **kwargs: str | bool
    ) -> list[str]:
        cmd = [self.python, "-m", module]
        cmd.extend(args)
        for key, value in kwargs.items():
            key_name = key.replace("_", "-")
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{key_name}")
            else:
                cmd.extend([f"--{key_name}", str(value)])
        return cmd

    def run_module(self, module: str, *args: str, **kwargs: Any) -> CLIResult:
        """汎用モジュール実行"""
        return self._run(self._build_module_args(module, *args, **kwargs))
