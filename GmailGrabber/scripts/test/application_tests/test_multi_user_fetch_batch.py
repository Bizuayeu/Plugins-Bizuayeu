#!/usr/bin/env python3
"""
application/fetch/multi_user_fetch_batch.py テスト
==================================================
"""

from datetime import date, datetime, timezone

import pytest

from application.fetch.multi_user_fetch_batch import (
    STATE_SAVE_INTERVAL_MULTI,
    MultiUserFetchBatchUseCase,
)
from domain.exceptions import InvalidBackupPlanError
from domain.types.account import GmailAccount
from domain.types.multi_backup import MultiUserBackupPlan, MultiUserBackupState
from domain.types.query import SearchQuery
from test.test_helpers import (
    FakeClock,
    FakeGmailClient,
    FakeGmailClientFactory,
    FakeMessageWriter,
    FakeMultiUserStateRepository,
    make_gmail_message,
    make_message_with_id,
)


def _account(email: str) -> GmailAccount:
    return {
        "email": email,
        "label": email.split("@")[0],
        "credentials_path": "/tmp/cs.json",
        "token_path": "/tmp/tok.json",
    }


def _query() -> SearchQuery:
    return {
        "from_addr": None,
        "to_addr": None,
        "subject": None,
        "label": None,
        "date_range": {"start": date(2026, 4, 1), "end": date(2026, 4, 12)},
        "has_attachment": None,
        "raw_query": None,
    }


def _plan(accounts: list[GmailAccount]) -> MultiUserBackupPlan:
    return {
        "multi_plan_id": "multi_plan_20260411_test01",
        "accounts": accounts,
        "query": _query(),
        "output_dir": "/tmp/output",
        "output_format": "eml",
    }


# =============================================================================
# Validation
# =============================================================================


class TestMultiUserValidation:
    @pytest.mark.unit
    def test_empty_accounts_raises(self) -> None:
        uc = MultiUserFetchBatchUseCase(
            FakeGmailClientFactory(),
            FakeMessageWriter(),
            FakeMultiUserStateRepository(),
            FakeClock(),
        )
        plan = _plan([])
        with pytest.raises(InvalidBackupPlanError, match="accounts"):
            uc.execute(plan, state_dir="/tmp/state")

    @pytest.mark.unit
    def test_empty_multi_plan_id_raises(self) -> None:
        uc = MultiUserFetchBatchUseCase(
            FakeGmailClientFactory(),
            FakeMessageWriter(),
            FakeMultiUserStateRepository(),
            FakeClock(),
        )
        plan = _plan([_account("a@m.com")])
        plan["multi_plan_id"] = ""
        with pytest.raises(InvalidBackupPlanError, match="multi_plan_id"):
            uc.execute(plan, state_dir="/tmp/state")

    @pytest.mark.unit
    def test_duplicate_emails_raises(self) -> None:
        uc = MultiUserFetchBatchUseCase(
            FakeGmailClientFactory(),
            FakeMessageWriter(),
            FakeMultiUserStateRepository(),
            FakeClock(),
        )
        plan = _plan([_account("a@m.com"), _account("a@m.com")])
        with pytest.raises(InvalidBackupPlanError, match="duplicate"):
            uc.execute(plan, state_dir="/tmp/state")

    @pytest.mark.unit
    def test_invalid_format_raises(self) -> None:
        uc = MultiUserFetchBatchUseCase(
            FakeGmailClientFactory(),
            FakeMessageWriter(),
            FakeMultiUserStateRepository(),
            FakeClock(),
        )
        plan = _plan([_account("a@m.com")])
        plan["output_format"] = "txt"  # type: ignore[typeddict-item]
        with pytest.raises(InvalidBackupPlanError, match="output_format"):
            uc.execute(plan, state_dir="/tmp/state")


# =============================================================================
# Happy path
# =============================================================================


class TestMultiUserHappyPath:
    @pytest.mark.unit
    def test_single_user_no_dedup(self) -> None:
        msgs = [make_message_with_id(f"id{i}", f"<m{i}@ex.com>") for i in range(3)]
        client = FakeGmailClient(messages=msgs)
        factory = FakeGmailClientFactory({"alice@m.com": client})
        writer = FakeMessageWriter()
        uc = MultiUserFetchBatchUseCase(
            factory, writer, FakeMultiUserStateRepository(), FakeClock()
        )

        result = uc.execute(_plan([_account("alice@m.com")]), state_dir="/tmp/state")

        assert result["per_user_success"] == {"alice@m.com": 3}
        assert result["per_user_deduped"] == {"alice@m.com": 0}
        assert result["total_unique_messages"] == 3
        assert result["total_dedup_skipped"] == 0
        assert len(writer.written) == 3

    @pytest.mark.unit
    def test_two_users_no_overlap(self) -> None:
        alice_msgs = [make_message_with_id(f"a{i}", f"<a{i}@ex.com>") for i in range(3)]
        bob_msgs = [make_message_with_id(f"b{i}", f"<b{i}@ex.com>") for i in range(2)]
        factory = FakeGmailClientFactory(
            {
                "alice@m.com": FakeGmailClient(messages=alice_msgs),
                "bob@m.com": FakeGmailClient(messages=bob_msgs),
            }
        )
        writer = FakeMessageWriter()
        uc = MultiUserFetchBatchUseCase(
            factory, writer, FakeMultiUserStateRepository(), FakeClock()
        )

        result = uc.execute(
            _plan([_account("alice@m.com"), _account("bob@m.com")]),
            state_dir="/tmp/state",
        )

        assert result["per_user_success"] == {"alice@m.com": 3, "bob@m.com": 2}
        assert result["per_user_deduped"] == {"alice@m.com": 0, "bob@m.com": 0}
        assert result["total_unique_messages"] == 5
        assert result["total_dedup_skipped"] == 0

    @pytest.mark.unit
    def test_two_users_full_overlap_first_wins(self) -> None:
        """同じ Message-ID を両ユーザーが持つ → 先処理ユーザー (alice) のみ書き込み"""
        msg1 = make_message_with_id("alice_id1", "<shared1@ex.com>")
        msg2 = make_message_with_id("alice_id2", "<shared2@ex.com>")
        msg1_bob = make_message_with_id("bob_id1", "<shared1@ex.com>")
        msg2_bob = make_message_with_id("bob_id2", "<shared2@ex.com>")

        factory = FakeGmailClientFactory(
            {
                "alice@m.com": FakeGmailClient(messages=[msg1, msg2]),
                "bob@m.com": FakeGmailClient(messages=[msg1_bob, msg2_bob]),
            }
        )
        writer = FakeMessageWriter()
        uc = MultiUserFetchBatchUseCase(
            factory, writer, FakeMultiUserStateRepository(), FakeClock()
        )

        result = uc.execute(
            _plan([_account("alice@m.com"), _account("bob@m.com")]),
            state_dir="/tmp/state",
        )

        assert result["per_user_success"]["alice@m.com"] == 2
        assert result["per_user_success"]["bob@m.com"] == 0
        assert result["per_user_deduped"]["alice@m.com"] == 0
        assert result["per_user_deduped"]["bob@m.com"] == 2
        assert result["total_unique_messages"] == 2
        assert result["total_dedup_skipped"] == 2
        # alice の版のみ書き込まれる
        assert len(writer.written) == 2
        written_ids = {m["gmail_id"] for m in writer.written}
        assert written_ids == {"alice_id1", "alice_id2"}

    @pytest.mark.unit
    def test_three_users_partial_overlaps(self) -> None:
        """
        alice: m1, m2, m3
        bob:   m2, m3, m4
        carol: m3, m4, m5
        → alice=3 書込, bob=1 (m4), carol=1 (m5), total=5, dedup=4
        """
        alice_msgs = [
            make_message_with_id("a1", "<m1@ex.com>"),
            make_message_with_id("a2", "<m2@ex.com>"),
            make_message_with_id("a3", "<m3@ex.com>"),
        ]
        bob_msgs = [
            make_message_with_id("b2", "<m2@ex.com>"),
            make_message_with_id("b3", "<m3@ex.com>"),
            make_message_with_id("b4", "<m4@ex.com>"),
        ]
        carol_msgs = [
            make_message_with_id("c3", "<m3@ex.com>"),
            make_message_with_id("c4", "<m4@ex.com>"),
            make_message_with_id("c5", "<m5@ex.com>"),
        ]
        factory = FakeGmailClientFactory(
            {
                "alice@m.com": FakeGmailClient(messages=alice_msgs),
                "bob@m.com": FakeGmailClient(messages=bob_msgs),
                "carol@m.com": FakeGmailClient(messages=carol_msgs),
            }
        )
        writer = FakeMessageWriter()
        uc = MultiUserFetchBatchUseCase(
            factory, writer, FakeMultiUserStateRepository(), FakeClock()
        )

        result = uc.execute(
            _plan([_account("alice@m.com"), _account("bob@m.com"), _account("carol@m.com")]),
            state_dir="/tmp/state",
        )

        assert result["per_user_success"]["alice@m.com"] == 3
        assert result["per_user_success"]["bob@m.com"] == 1
        assert result["per_user_success"]["carol@m.com"] == 1
        assert result["per_user_deduped"]["alice@m.com"] == 0
        assert result["per_user_deduped"]["bob@m.com"] == 2
        assert result["per_user_deduped"]["carol@m.com"] == 2
        assert result["total_unique_messages"] == 5
        assert result["total_dedup_skipped"] == 4

    @pytest.mark.unit
    def test_user_order_preserved_from_plan(self) -> None:
        factory = FakeGmailClientFactory()
        uc = MultiUserFetchBatchUseCase(
            factory, FakeMessageWriter(), FakeMultiUserStateRepository(), FakeClock()
        )

        uc.execute(
            _plan([_account("z@m.com"), _account("a@m.com"), _account("m@m.com")]),
            state_dir="/tmp/state",
        )

        assert factory.create_calls == ["z@m.com", "a@m.com", "m@m.com"]

    @pytest.mark.unit
    def test_factory_called_once_per_user(self) -> None:
        factory = FakeGmailClientFactory()
        uc = MultiUserFetchBatchUseCase(
            factory, FakeMessageWriter(), FakeMultiUserStateRepository(), FakeClock()
        )

        uc.execute(
            _plan([_account("a@m.com"), _account("b@m.com")]),
            state_dir="/tmp/state",
        )

        assert len(factory.create_calls) == 2


# =============================================================================
# Resume
# =============================================================================


class TestMultiUserResume:
    @pytest.mark.unit
    def test_resume_skips_completed_users(self) -> None:
        alice_msgs = [make_message_with_id(f"a{i}", f"<a{i}@ex.com>") for i in range(3)]
        bob_msgs = [make_message_with_id(f"b{i}", f"<b{i}@ex.com>") for i in range(2)]
        factory = FakeGmailClientFactory(
            {
                "alice@m.com": FakeGmailClient(messages=alice_msgs),
                "bob@m.com": FakeGmailClient(messages=bob_msgs),
            }
        )
        writer = FakeMessageWriter()
        state_repo = FakeMultiUserStateRepository()

        # 既存 state: alice 完了済み
        existing: MultiUserBackupState = {
            "multi_plan_id": "multi_plan_20260411_test01",
            "per_user_states": {
                "alice@m.com": {
                    "plan_id": "multi_plan_20260411_test01__alice@m.com",
                    "fetched_ids": ["a0", "a1", "a2"],
                    "failed_ids": [],
                    "last_updated": datetime(2026, 4, 11, 9, 0, tzinfo=timezone.utc),
                    "total_estimated": 3,
                }
            },
            "message_id_index": {
                "<a0@ex.com>": "alice@m.com::a0",
                "<a1@ex.com>": "alice@m.com::a1",
                "<a2@ex.com>": "alice@m.com::a2",
            },
            "last_updated": datetime(2026, 4, 11, 9, 0, tzinfo=timezone.utc),
            "started_user_emails": ["alice@m.com"],
            "completed_user_emails": ["alice@m.com"],
        }
        state_repo.save(existing, "/tmp/state")

        uc = MultiUserFetchBatchUseCase(factory, writer, state_repo, FakeClock())
        result = uc.execute(
            _plan([_account("alice@m.com"), _account("bob@m.com")]),
            state_dir="/tmp/state",
            resume=True,
        )

        assert result["per_user_success"]["alice@m.com"] == 0  # スキップ
        assert result["per_user_success"]["bob@m.com"] == 2  # 新規処理
        assert len(writer.written) == 2  # alice の再書き込みは無い

    @pytest.mark.unit
    def test_resume_dedup_across_restart(self) -> None:
        """再開時に message_id_index が継続されていれば、bob で alice が持つ message は dedup される"""
        # alice は既に `<shared@ex.com>` を index 済み
        shared_msg_bob = make_message_with_id("bob_shared", "<shared@ex.com>")
        other_msg_bob = make_message_with_id("bob_new", "<new@ex.com>")

        factory = FakeGmailClientFactory(
            {"bob@m.com": FakeGmailClient(messages=[shared_msg_bob, other_msg_bob])}
        )
        writer = FakeMessageWriter()
        state_repo = FakeMultiUserStateRepository()
        existing: MultiUserBackupState = {
            "multi_plan_id": "multi_plan_20260411_test01",
            "per_user_states": {},
            "message_id_index": {"<shared@ex.com>": "alice@m.com::some_id"},
            "last_updated": datetime(2026, 4, 11, 9, 0, tzinfo=timezone.utc),
            "started_user_emails": ["alice@m.com"],
            "completed_user_emails": ["alice@m.com"],
        }
        state_repo.save(existing, "/tmp/state")

        uc = MultiUserFetchBatchUseCase(factory, writer, state_repo, FakeClock())
        result = uc.execute(
            _plan([_account("alice@m.com"), _account("bob@m.com")]),
            state_dir="/tmp/state",
            resume=True,
        )

        assert result["per_user_success"]["bob@m.com"] == 1  # new のみ
        assert result["per_user_deduped"]["bob@m.com"] == 1  # shared は dedup

    @pytest.mark.unit
    def test_resume_false_ignores_existing_state(self) -> None:
        msgs = [make_message_with_id(f"a{i}", f"<a{i}@ex.com>") for i in range(2)]
        factory = FakeGmailClientFactory({"alice@m.com": FakeGmailClient(messages=msgs)})
        writer = FakeMessageWriter()
        state_repo = FakeMultiUserStateRepository()

        existing: MultiUserBackupState = {
            "multi_plan_id": "multi_plan_20260411_test01",
            "per_user_states": {},
            "message_id_index": {},
            "last_updated": datetime(2026, 4, 11, 9, 0, tzinfo=timezone.utc),
            "started_user_emails": ["alice@m.com"],
            "completed_user_emails": ["alice@m.com"],
        }
        state_repo.save(existing, "/tmp/state")

        uc = MultiUserFetchBatchUseCase(factory, writer, state_repo, FakeClock())
        result = uc.execute(
            _plan([_account("alice@m.com")]),
            state_dir="/tmp/state",
            resume=False,
        )

        # 完全に新規実行 → 既存 completed_user_emails は無視される
        assert result["per_user_success"]["alice@m.com"] == 2


# =============================================================================
# Failures
# =============================================================================


class TestMultiUserFailures:
    @pytest.mark.unit
    def test_auth_failure_one_user_continues(self) -> None:
        bob_msgs = [make_message_with_id("b1", "<m1@ex.com>")]
        factory = FakeGmailClientFactory(
            {"bob@m.com": FakeGmailClient(messages=bob_msgs)},
            fail_on_users={"alice@m.com"},
        )
        uc = MultiUserFetchBatchUseCase(
            factory, FakeMessageWriter(), FakeMultiUserStateRepository(), FakeClock()
        )

        result = uc.execute(
            _plan([_account("alice@m.com"), _account("bob@m.com")]),
            state_dir="/tmp/state",
        )

        assert result["per_user_failure"]["alice@m.com"] == 1
        assert result["per_user_success"]["bob@m.com"] == 1

    @pytest.mark.unit
    def test_fetch_failure_continues_other_users(self) -> None:
        alice_msgs = [make_message_with_id(f"a{i}", f"<a{i}@ex.com>") for i in range(3)]
        bob_msgs = [make_message_with_id("b1", "<b1@ex.com>")]
        factory = FakeGmailClientFactory(
            {
                "alice@m.com": FakeGmailClient(messages=alice_msgs, fetch_failures={"a1"}),
                "bob@m.com": FakeGmailClient(messages=bob_msgs),
            }
        )
        uc = MultiUserFetchBatchUseCase(
            factory, FakeMessageWriter(), FakeMultiUserStateRepository(), FakeClock()
        )

        result = uc.execute(
            _plan([_account("alice@m.com"), _account("bob@m.com")]),
            state_dir="/tmp/state",
        )

        assert result["per_user_success"]["alice@m.com"] == 2
        assert result["per_user_failure"]["alice@m.com"] == 1
        assert result["per_user_success"]["bob@m.com"] == 1

    @pytest.mark.unit
    def test_message_without_message_id_written_and_counted(self) -> None:
        """Message-ID ヘッダ無しのメールも強制書き込みされる"""
        no_mid_msg = make_gmail_message(
            "nomid_id",
            raw_mime=b"From: test@ex.com\r\nSubject: no id\r\n\r\nbody",
        )
        factory = FakeGmailClientFactory({"alice@m.com": FakeGmailClient(messages=[no_mid_msg])})
        writer = FakeMessageWriter()
        uc = MultiUserFetchBatchUseCase(
            factory, writer, FakeMultiUserStateRepository(), FakeClock()
        )

        result = uc.execute(
            _plan([_account("alice@m.com")]),
            state_dir="/tmp/state",
        )

        assert result["per_user_success"]["alice@m.com"] == 1
        assert result["total_messages_without_message_id"] == 1
        assert len(writer.written) == 1


# =============================================================================
# Dedup correctness
# =============================================================================


class TestDedupCorrectness:
    @pytest.mark.unit
    def test_case_insensitive_domain(self) -> None:
        """<ABC@Example.COM> と <ABC@example.com> は同一メッセージ"""
        msg1 = make_message_with_id("a1", "<ABC@Example.COM>")
        msg2 = make_message_with_id("b1", "<ABC@example.com>")
        factory = FakeGmailClientFactory(
            {
                "alice@m.com": FakeGmailClient(messages=[msg1]),
                "bob@m.com": FakeGmailClient(messages=[msg2]),
            }
        )
        writer = FakeMessageWriter()
        uc = MultiUserFetchBatchUseCase(
            factory, writer, FakeMultiUserStateRepository(), FakeClock()
        )

        result = uc.execute(
            _plan([_account("alice@m.com"), _account("bob@m.com")]),
            state_dir="/tmp/state",
        )

        assert result["per_user_success"]["alice@m.com"] == 1
        assert result["per_user_deduped"]["bob@m.com"] == 1
        assert len(writer.written) == 1

    @pytest.mark.unit
    def test_local_part_case_matters(self) -> None:
        """<ABC@example.com> と <abc@example.com> はローカル部が異なるので別メッセージ"""
        msg1 = make_message_with_id("a1", "<ABC@example.com>")
        msg2 = make_message_with_id("b1", "<abc@example.com>")
        factory = FakeGmailClientFactory(
            {
                "alice@m.com": FakeGmailClient(messages=[msg1]),
                "bob@m.com": FakeGmailClient(messages=[msg2]),
            }
        )
        writer = FakeMessageWriter()
        uc = MultiUserFetchBatchUseCase(
            factory, writer, FakeMultiUserStateRepository(), FakeClock()
        )

        result = uc.execute(
            _plan([_account("alice@m.com"), _account("bob@m.com")]),
            state_dir="/tmp/state",
        )

        assert result["per_user_success"]["alice@m.com"] == 1
        assert result["per_user_success"]["bob@m.com"] == 1
        assert len(writer.written) == 2

    @pytest.mark.unit
    def test_message_id_index_tracks_owner(self) -> None:
        """index には「誰が最初にとったか」が記録される"""
        msg = make_message_with_id("a1", "<shared@ex.com>")
        factory = FakeGmailClientFactory({"alice@m.com": FakeGmailClient(messages=[msg])})
        state_repo = FakeMultiUserStateRepository()
        uc = MultiUserFetchBatchUseCase(factory, FakeMessageWriter(), state_repo, FakeClock())

        uc.execute(
            _plan([_account("alice@m.com")]),
            state_dir="/tmp/state",
        )

        saved = state_repo.load("multi_plan_20260411_test01", "/tmp/state")
        assert saved is not None
        assert "<shared@ex.com>" in saved["message_id_index"]
        assert saved["message_id_index"]["<shared@ex.com>"] == "alice@m.com::a1"

    @pytest.mark.unit
    def test_first_wins_policy(self) -> None:
        """message_id_index の value は最初に遭遇した user のものに保たれる"""
        msg_alice = make_message_with_id("alice_id", "<shared@ex.com>")
        msg_bob = make_message_with_id("bob_id", "<shared@ex.com>")
        factory = FakeGmailClientFactory(
            {
                "alice@m.com": FakeGmailClient(messages=[msg_alice]),
                "bob@m.com": FakeGmailClient(messages=[msg_bob]),
            }
        )
        state_repo = FakeMultiUserStateRepository()
        uc = MultiUserFetchBatchUseCase(factory, FakeMessageWriter(), state_repo, FakeClock())

        uc.execute(
            _plan([_account("alice@m.com"), _account("bob@m.com")]),
            state_dir="/tmp/state",
        )

        saved = state_repo.load("multi_plan_20260411_test01", "/tmp/state")
        assert saved is not None
        # alice が先行、alice の gmail_id が index に残る
        assert saved["message_id_index"]["<shared@ex.com>"] == "alice@m.com::alice_id"
