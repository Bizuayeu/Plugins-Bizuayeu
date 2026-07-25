#!/usr/bin/env python3
"""
FetchBatchUseCase
=================

バックアップ計画を受け取り、Gmail API からメッセージをバッチ取得して書き出す
メインユースケース。

責務:
1. BackupPlan の SearchQuery を Gmail クエリ文字列に変換
2. 既存の BackupState をロード（resume=True かつ存在する場合）
3. 未取得メッセージIDを Gmail API から列挙
4. 1件ずつ fetch → writer.write → state 更新（冪等性確保）
5. writer.finalize を呼び出して最終ファイルパス列を取得
6. BackupResult を返す

設計:
- GmailClientProtocol, MessageWriterProtocol, StateRepositoryProtocol, ClockProtocol
  を DI で受け取り、テストで Fake に差し替え可能
- state は一定件数ごとに保存（I/O 負荷軽減）
- 失敗したメッセージは failed_ids に追記し、処理継続
"""

from typing import Final, Optional

from domain.exceptions import InvalidBackupPlanError
from domain.protocols import (
    ClockProtocol,
    GmailClientProtocol,
    MessageWriterProtocol,
    StateRepositoryProtocol,
)
from domain.query_builder import build_gmail_query
from domain.types.backup import BackupPlan, BackupResult, BackupState

STATE_SAVE_INTERVAL: Final[int] = 10  # N件ごとに state を保存


class FetchBatchUseCase:
    """Gmail メッセージのバッチ取得ユースケース"""

    def __init__(
        self,
        gmail_client: GmailClientProtocol,
        writer: MessageWriterProtocol,
        state_repo: StateRepositoryProtocol,
        clock: ClockProtocol,
    ) -> None:
        self._client = gmail_client
        self._writer = writer
        self._state_repo = state_repo
        self._clock = clock

    def execute(
        self,
        plan: BackupPlan,
        state_dir: str,
        resume: bool = True,
        max_messages: Optional[int] = None,
    ) -> BackupResult:
        """
        バックアップ計画を実行する。

        Args:
            plan: 実行する BackupPlan
            state_dir: BackupState 保存先ディレクトリ
            resume: True なら既存 state から再開、False なら新規実行
            max_messages: 取得上限（None = 無制限）

        Returns:
            BackupResult

        Raises:
            InvalidBackupPlanError: plan のバリデーション失敗
        """
        self._validate_plan(plan)

        started_at = self._clock.now()
        query_string = build_gmail_query(plan["query"])

        # State の初期化 or 再開
        state = self._load_or_init_state(plan, resume, state_dir)
        fetched_set: set[str] = set(state["fetched_ids"])
        failed_list: list[str] = list(state["failed_ids"])

        output_files: list[str] = []
        new_success_count = 0
        new_failure_count = 0
        processed_since_save = 0

        # 推定件数を取得（total_estimated 更新用）
        try:
            state["total_estimated"] = self._client.estimate_count(query_string)
        except Exception:
            pass  # 推定失敗は致命的ではない

        # メッセージID列挙 → 1件ずつ処理
        for msg_id in self._client.list_message_ids(query_string):
            if max_messages is not None and new_success_count >= max_messages:
                break

            if msg_id in fetched_set:
                continue  # 冪等性: 既取得はスキップ

            try:
                msg = self._client.fetch_message(msg_id)
                path = self._writer.write(msg, plan["output_dir"])
                output_files.append(path)
                fetched_set.add(msg_id)
                new_success_count += 1
            except Exception:
                if msg_id not in failed_list:
                    failed_list.append(msg_id)
                new_failure_count += 1

            processed_since_save += 1
            if processed_since_save >= STATE_SAVE_INTERVAL:
                state["fetched_ids"] = sorted(fetched_set)
                state["failed_ids"] = failed_list
                state["last_updated"] = self._clock.now()
                self._state_repo.save(state, state_dir)
                processed_since_save = 0

        # 最終 state 保存
        state["fetched_ids"] = sorted(fetched_set)
        state["failed_ids"] = failed_list
        state["last_updated"] = self._clock.now()
        self._state_repo.save(state, state_dir)

        # Writer 最終化（mbox のクローズ等）
        finalized_files = self._writer.finalize(plan["output_dir"])
        if finalized_files:
            output_files = finalized_files

        finished_at = self._clock.now()

        return {
            "plan_id": plan["plan_id"],
            "success_count": new_success_count,
            "failure_count": new_failure_count,
            "output_files": output_files,
            "started_at": started_at,
            "finished_at": finished_at,
        }

    # =========================================================================
    # helpers
    # =========================================================================

    def _validate_plan(self, plan: BackupPlan) -> None:
        if not plan.get("plan_id"):
            raise InvalidBackupPlanError("plan_id is empty")
        if not plan.get("output_dir"):
            raise InvalidBackupPlanError("output_dir is empty")
        if plan.get("output_format") not in ("eml", "mbox"):
            raise InvalidBackupPlanError(
                f"output_format must be 'eml' or 'mbox', got {plan.get('output_format')}"
            )

    def _load_or_init_state(self, plan: BackupPlan, resume: bool, state_dir: str) -> BackupState:
        if resume:
            existing = self._state_repo.load(plan["plan_id"], state_dir)
            if existing is not None:
                return existing

        return {
            "plan_id": plan["plan_id"],
            "fetched_ids": [],
            "failed_ids": [],
            "last_updated": self._clock.now(),
            "total_estimated": 0,
        }


__all__ = ["FetchBatchUseCase", "STATE_SAVE_INTERVAL"]
