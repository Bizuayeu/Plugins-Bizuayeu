#!/usr/bin/env python3
"""
MultiUserFetchBatchUseCase
==========================

複数ユーザー Gmail バックアップ + RFC5322 Message-ID 重複排除ユースケース。

責務:
1. MultiUserBackupPlan の accounts を順次 impersonate して処理
2. 各 user の GmailClient は GmailClientFactoryProtocol から取得 (Service Account 経由)
3. fetch_message 後、extract_message_id → normalize_message_id で正規化
4. MultiUserBackupState.message_id_index で「最初に遭遇した版」優先の dedup
5. Message-ID 欠落メールは dedup 対象外、強制書き込み + 警告出力
6. 認証失敗・API 失敗は per_user_failure に記録、他ユーザーは継続
7. 中断再開: multi_state の fetched_ids (user単位) と message_id_index (plan全体) で冪等

設計:
- 既存 FetchBatchUseCase とは独立 (クラスの import すらしない)
- Clean Architecture: GmailClientFactoryProtocol, MessageWriterProtocol,
  MultiUserStateRepositoryProtocol, ClockProtocol を DI で受け取る
- state は STATE_SAVE_INTERVAL_MULTI 件ごとに保存
"""

import sys
from typing import Final

from domain.exceptions import InvalidBackupPlanError
from domain.message_id_parser import extract_message_id, normalize_message_id
from domain.protocols import (
    ClockProtocol,
    GmailClientFactoryProtocol,
    MessageWriterProtocol,
    MultiUserStateRepositoryProtocol,
)
from domain.query_builder import build_gmail_query
from domain.types.account import GmailAccount
from domain.types.backup import BackupState
from domain.types.multi_backup import (
    MultiUserBackupPlan,
    MultiUserBackupResult,
    MultiUserBackupState,
)

STATE_SAVE_INTERVAL_MULTI: Final[int] = 20


class MultiUserFetchBatchUseCase:
    """複数ユーザー Gmail バックアップ + Message-ID 重複排除"""

    def __init__(
        self,
        client_factory: GmailClientFactoryProtocol,
        writer: MessageWriterProtocol,
        multi_state_repo: MultiUserStateRepositoryProtocol,
        clock: ClockProtocol,
    ) -> None:
        self._factory = client_factory
        self._writer = writer
        self._multi_repo = multi_state_repo
        self._clock = clock

    def execute(
        self,
        plan: MultiUserBackupPlan,
        state_dir: str,
        resume: bool = True,
        max_messages_per_user: int | None = None,
    ) -> MultiUserBackupResult:
        """
        複数ユーザーバックアップを実行する。

        Args:
            plan: MultiUserBackupPlan
            state_dir: MultiUserBackupState 保存先
            resume: True なら既存 state から再開
            max_messages_per_user: 各ユーザーごとの取得上限

        Returns:
            MultiUserBackupResult

        Raises:
            InvalidBackupPlanError: plan のバリデーション失敗
        """
        self._validate_plan(plan)

        started_at = self._clock.now()
        query_string = build_gmail_query(plan["query"])

        state = self._load_or_init_state(plan, resume, state_dir)

        per_user_success: dict[str, int] = {}
        per_user_failure: dict[str, int] = {}
        per_user_deduped: dict[str, int] = {}
        per_user_no_message_id: dict[str, int] = {}

        output_files: list[str] = []

        for account in plan["accounts"]:
            user_email = account["email"]

            if user_email not in state["started_user_emails"]:
                state["started_user_emails"].append(user_email)

            if user_email in state["completed_user_emails"] and resume:
                per_user_success[user_email] = 0
                per_user_failure[user_email] = 0
                per_user_deduped[user_email] = 0
                per_user_no_message_id[user_email] = 0
                continue

            success, failure, deduped, no_mid = self._process_user(
                account=account,
                query_string=query_string,
                plan=plan,
                state=state,
                state_dir=state_dir,
                max_messages=max_messages_per_user,
            )
            per_user_success[user_email] = success
            per_user_failure[user_email] = failure
            per_user_deduped[user_email] = deduped
            per_user_no_message_id[user_email] = no_mid

            if user_email not in state["completed_user_emails"]:
                state["completed_user_emails"].append(user_email)

            state["last_updated"] = self._clock.now()
            self._multi_repo.save(state, state_dir)

        finalized = self._writer.finalize(plan["output_dir"])
        if finalized:
            output_files = finalized

        finished_at = self._clock.now()

        total_unique = sum(per_user_success.values())
        total_dedup = sum(per_user_deduped.values())
        total_no_mid = sum(per_user_no_message_id.values())

        return {
            "multi_plan_id": plan["multi_plan_id"],
            "per_user_success": per_user_success,
            "per_user_failure": per_user_failure,
            "per_user_deduped": per_user_deduped,
            "total_unique_messages": total_unique,
            "total_dedup_skipped": total_dedup,
            "total_messages_without_message_id": total_no_mid,
            "output_files": output_files,
            "started_at": started_at,
            "finished_at": finished_at,
        }

    # =========================================================================
    # Internal helpers
    # =========================================================================

    def _validate_plan(self, plan: MultiUserBackupPlan) -> None:
        if not plan.get("multi_plan_id"):
            raise InvalidBackupPlanError("multi_plan_id is empty")
        if not plan.get("output_dir"):
            raise InvalidBackupPlanError("output_dir is empty")
        if plan.get("output_format") not in ("eml", "mbox"):
            raise InvalidBackupPlanError(
                f"output_format must be 'eml' or 'mbox', got {plan.get('output_format')}"
            )
        accounts = plan.get("accounts", [])
        if not accounts:
            raise InvalidBackupPlanError("accounts is empty")
        emails = [a["email"] for a in accounts]
        if len(emails) != len(set(emails)):
            raise InvalidBackupPlanError(f"duplicate account emails: {emails}")

    def _load_or_init_state(
        self, plan: MultiUserBackupPlan, resume: bool, state_dir: str
    ) -> MultiUserBackupState:
        if resume:
            existing = self._multi_repo.load(plan["multi_plan_id"], state_dir)
            if existing is not None:
                return existing

        return {
            "multi_plan_id": plan["multi_plan_id"],
            "per_user_states": {},
            "message_id_index": {},
            "last_updated": self._clock.now(),
            "started_user_emails": [],
            "completed_user_emails": [],
        }

    def _process_user(
        self,
        account: GmailAccount,
        query_string: str,
        plan: MultiUserBackupPlan,
        state: MultiUserBackupState,
        state_dir: str,
        max_messages: int | None,
    ) -> tuple[int, int, int, int]:
        """
        1ユーザー分を処理する。

        Returns:
            (success, failure, deduped, no_message_id_count)
        """
        user_email = account["email"]

        # Gmail client 取得 (失敗なら全カウント 0 + failure 1)
        try:
            client = self._factory.create_for_user(user_email)
        except Exception as e:  # noqa: BLE001
            self._warn(f"auth failed for {user_email}: {e}")
            return 0, 1, 0, 0

        user_state = self._get_or_init_user_state(plan, user_email, state)
        fetched_set: set[str] = set(user_state["fetched_ids"])
        failed_list: list[str] = list(user_state["failed_ids"])

        success = 0
        failure = 0
        deduped = 0
        no_mid = 0
        processed_since_save = 0

        try:
            for msg_id in client.list_message_ids(query_string):
                if max_messages is not None and success >= max_messages:
                    break
                if msg_id in fetched_set:
                    continue

                try:
                    msg = client.fetch_message(msg_id)
                except Exception as e:  # noqa: BLE001
                    if msg_id not in failed_list:
                        failed_list.append(msg_id)
                    failure += 1
                    self._warn(f"fetch failed for {user_email}/{msg_id}: {e}")
                    continue

                raw_mid = extract_message_id(msg["raw_mime"])
                if raw_mid is None:
                    # Message-ID 欠落: dedup 対象外、強制書き込み
                    self._warn(
                        f"message {user_email}/{msg_id} has no Message-ID header; "
                        f"dedup skipped, saved as-is"
                    )
                    no_mid += 1
                    try:
                        self._writer.write(msg, plan["output_dir"])
                        fetched_set.add(msg_id)
                        success += 1
                    except Exception as e:  # noqa: BLE001
                        failure += 1
                        if msg_id not in failed_list:
                            failed_list.append(msg_id)
                        self._warn(f"write failed: {e}")
                    continue

                normalized = normalize_message_id(raw_mid)
                if normalized in state["message_id_index"]:
                    # 既に別ユーザー (or 同ユーザー) で取得済み
                    deduped += 1
                    fetched_set.add(msg_id)
                    continue

                # 新規: 書き込み + index 更新
                try:
                    self._writer.write(msg, plan["output_dir"])
                    fetched_set.add(msg_id)
                    state["message_id_index"][normalized] = f"{user_email}::{msg_id}"
                    success += 1
                except Exception as e:  # noqa: BLE001
                    failure += 1
                    if msg_id not in failed_list:
                        failed_list.append(msg_id)
                    self._warn(f"write failed for {user_email}/{msg_id}: {e}")

                processed_since_save += 1
                if processed_since_save >= STATE_SAVE_INTERVAL_MULTI:
                    user_state["fetched_ids"] = sorted(fetched_set)
                    user_state["failed_ids"] = failed_list
                    user_state["last_updated"] = self._clock.now()
                    state["last_updated"] = self._clock.now()
                    self._multi_repo.save(state, state_dir)
                    processed_since_save = 0
        except Exception as e:  # noqa: BLE001
            self._warn(f"list_message_ids failed for {user_email}: {e}")
            failure += 1

        # 最終 user_state 更新
        user_state["fetched_ids"] = sorted(fetched_set)
        user_state["failed_ids"] = failed_list
        user_state["last_updated"] = self._clock.now()
        state["per_user_states"][user_email] = user_state

        return success, failure, deduped, no_mid

    def _get_or_init_user_state(
        self,
        plan: MultiUserBackupPlan,
        user_email: str,
        state: MultiUserBackupState,
    ) -> BackupState:
        existing = state["per_user_states"].get(user_email)
        if existing is not None:
            return existing
        return {
            "plan_id": f"{plan['multi_plan_id']}__{user_email}",
            "fetched_ids": [],
            "failed_ids": [],
            "last_updated": self._clock.now(),
            "total_estimated": 0,
        }

    def _warn(self, message: str) -> None:
        print(f"WARN: {message}", file=sys.stderr)


__all__ = ["MultiUserFetchBatchUseCase", "STATE_SAVE_INTERVAL_MULTI"]
