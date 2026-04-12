#!/usr/bin/env python3
"""
application/resolver/resolver_service.py テスト
================================================

ResolverService の add/edit/remove/complete_archive/rebuild 動作検証。

設計意図:
- AliasResolverRepositoryProtocol を Fake で注入
- 全操作後の永続化（save_all 呼び出し）を検証
- 重複ID/未登録ID/論理削除/完工アーカイブのエッジケースをカバー
- property-based test で add → remove → add 安定性
"""

from typing import List

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from application.resolver.resolver_service import ResolverService
from domain.exceptions import EntityNotFoundError, ResolverError
from domain.types.alias import AliasRecord
from test.test_helpers import FakeAliasResolverRepository, build_alias_record

# =============================================================================
# add
# =============================================================================


class TestResolverServiceAdd:
    """add メソッドのテスト"""

    @pytest.mark.unit
    def test_add_single_record(self) -> None:
        repo = FakeAliasResolverRepository()
        svc = ResolverService(repo)
        rec = build_alias_record(slug="MaruMaru")
        svc.add(rec)
        all_records = repo.load_all()
        assert len(all_records) == 1
        assert all_records[0]["id"] == "projects/MaruMaru"

    @pytest.mark.unit
    def test_add_persists_via_save_all(self) -> None:
        """add 後 save_all が呼ばれている"""
        repo = FakeAliasResolverRepository()
        svc = ResolverService(repo)
        svc.add(build_alias_record(slug="A"))
        assert repo.save_count == 1

    @pytest.mark.unit
    def test_add_duplicate_id_raises(self) -> None:
        repo = FakeAliasResolverRepository(
            initial=[build_alias_record(slug="MaruMaru")]
        )
        svc = ResolverService(repo)
        with pytest.raises(ResolverError, match="duplicate"):
            svc.add(build_alias_record(slug="MaruMaru"))

    @pytest.mark.unit
    def test_add_validates_record(self) -> None:
        """不正レコードは ResolverError"""
        repo = FakeAliasResolverRepository()
        svc = ResolverService(repo)
        bad: AliasRecord = {  # type: ignore[typeddict-item]
            "id": "no_slash",
            "canonical": "X",
            "aliases": [],
            "shard": "projects",
            "target_path": "x",
            "archive_status": "active",
        }
        with pytest.raises(ResolverError):
            svc.add(bad)

    @pytest.mark.unit
    def test_add_multiple_different_records(self) -> None:
        repo = FakeAliasResolverRepository()
        svc = ResolverService(repo)
        svc.add(build_alias_record(slug="A"))
        svc.add(build_alias_record(slug="B"))
        svc.add(build_alias_record(kind="clients", slug="X"))
        assert len(repo.load_all()) == 3


# =============================================================================
# edit
# =============================================================================


class TestResolverServiceEdit:
    """edit メソッドのテスト"""

    @pytest.mark.unit
    def test_edit_canonical(self) -> None:
        repo = FakeAliasResolverRepository(
            initial=[build_alias_record(slug="A", canonical="旧名")]
        )
        svc = ResolverService(repo)
        svc.edit("projects/A", canonical="新名")
        rec = repo.load_all()[0]
        assert rec["canonical"] == "新名"

    @pytest.mark.unit
    def test_edit_appends_aliases(self) -> None:
        """edit で aliases にマージされる（重複は除外）"""
        repo = FakeAliasResolverRepository(
            initial=[build_alias_record(slug="A", aliases=["alias1"])]
        )
        svc = ResolverService(repo)
        svc.edit("projects/A", add_aliases=["alias2", "alias1", "alias3"])
        rec = repo.load_all()[0]
        assert set(rec["aliases"]) == {"alias1", "alias2", "alias3"}

    @pytest.mark.unit
    def test_edit_remove_aliases(self) -> None:
        repo = FakeAliasResolverRepository(
            initial=[build_alias_record(slug="A", aliases=["a1", "a2", "a3"])]
        )
        svc = ResolverService(repo)
        svc.edit("projects/A", remove_aliases=["a2"])
        rec = repo.load_all()[0]
        assert rec["aliases"] == ["a1", "a3"]

    @pytest.mark.unit
    def test_edit_unknown_id_raises(self) -> None:
        repo = FakeAliasResolverRepository()
        svc = ResolverService(repo)
        with pytest.raises(EntityNotFoundError):
            svc.edit("projects/Unknown", canonical="x")

    @pytest.mark.unit
    def test_edit_persists(self) -> None:
        repo = FakeAliasResolverRepository(
            initial=[build_alias_record(slug="A")]
        )
        svc = ResolverService(repo)
        before = repo.save_count
        svc.edit("projects/A", canonical="改")
        assert repo.save_count == before + 1

    @pytest.mark.unit
    def test_edit_target_path(self) -> None:
        """target_path 更新（active 同士での更新）"""
        repo = FakeAliasResolverRepository(
            initial=[build_alias_record(slug="A")]
        )
        svc = ResolverService(repo)
        svc.edit("projects/A", target_path="shards/projects/A_renamed/_project.md")
        rec = repo.load_all()[0]
        assert rec["target_path"] == "shards/projects/A_renamed/_project.md"


# =============================================================================
# remove
# =============================================================================


class TestResolverServiceRemove:
    """remove メソッドのテスト（論理削除 → archive_status="removed"）"""

    @pytest.mark.unit
    def test_remove_marks_removed(self) -> None:
        repo = FakeAliasResolverRepository(
            initial=[build_alias_record(slug="A", archive_status="active")]
        )
        svc = ResolverService(repo)
        svc.remove("projects/A")
        rec = repo.load_all()[0]
        assert rec["archive_status"] == "removed"

    @pytest.mark.unit
    def test_remove_does_not_delete(self) -> None:
        """論理削除なので物理的に消えない"""
        repo = FakeAliasResolverRepository(
            initial=[build_alias_record(slug="A")]
        )
        svc = ResolverService(repo)
        svc.remove("projects/A")
        assert len(repo.load_all()) == 1

    @pytest.mark.unit
    def test_remove_unknown_id_raises(self) -> None:
        repo = FakeAliasResolverRepository()
        svc = ResolverService(repo)
        with pytest.raises(EntityNotFoundError):
            svc.remove("projects/Unknown")

    @pytest.mark.unit
    def test_remove_already_removed_is_noop(self) -> None:
        """既に removed でも例外なく成功（idempotent）"""
        repo = FakeAliasResolverRepository(
            initial=[build_alias_record(slug="A", archive_status="removed")]
        )
        svc = ResolverService(repo)
        svc.remove("projects/A")  # raisesなし
        assert repo.load_all()[0]["archive_status"] == "removed"


# =============================================================================
# complete_archive (v4 新規)
# =============================================================================


class TestResolverServiceCompleteArchive:
    """complete_archive メソッドのテスト（完工アーカイブ）"""

    @pytest.mark.unit
    def test_complete_archive_sets_status_and_target_path(self) -> None:
        """archive_status='completed' と target_path が archive/ に更新される"""
        repo = FakeAliasResolverRepository(
            initial=[build_alias_record(slug="A", archive_status="active")]
        )
        svc = ResolverService(repo)
        svc.complete_archive(
            "projects/A",
            new_target_path="archive/projects/A/_project.md",
        )
        rec = repo.load_all()[0]
        assert rec["archive_status"] == "completed"
        assert rec["target_path"] == "archive/projects/A/_project.md"

    @pytest.mark.unit
    def test_complete_archive_unknown_id_raises(self) -> None:
        repo = FakeAliasResolverRepository()
        svc = ResolverService(repo)
        with pytest.raises(EntityNotFoundError):
            svc.complete_archive(
                "projects/Unknown",
                new_target_path="archive/projects/Unknown/_project.md",
            )

    @pytest.mark.unit
    def test_complete_archive_rejects_non_archive_target_path(self) -> None:
        """target_path が archive/ 接頭辞でない場合 ResolverError"""
        repo = FakeAliasResolverRepository(
            initial=[build_alias_record(slug="A")]
        )
        svc = ResolverService(repo)
        with pytest.raises(ResolverError):
            svc.complete_archive(
                "projects/A",
                new_target_path="shards/projects/A/_project.md",
            )

    @pytest.mark.unit
    def test_complete_archive_persists(self) -> None:
        repo = FakeAliasResolverRepository(
            initial=[build_alias_record(slug="A")]
        )
        svc = ResolverService(repo)
        before = repo.save_count
        svc.complete_archive(
            "projects/A",
            new_target_path="archive/projects/A/_project.md",
        )
        assert repo.save_count == before + 1

    @pytest.mark.unit
    def test_complete_archive_after_remove_transitions(self) -> None:
        """removed → completed は complete_archive() で可能（removed フラグは上書き）

        実務上はほぼ発生しないが、archive_status 状態遷移の自由度を保証する。
        """
        repo = FakeAliasResolverRepository(
            initial=[build_alias_record(slug="A", archive_status="removed")]
        )
        svc = ResolverService(repo)
        svc.complete_archive(
            "projects/A",
            new_target_path="archive/projects/A/_project.md",
        )
        rec = repo.load_all()[0]
        assert rec["archive_status"] == "completed"


# =============================================================================
# rebuild
# =============================================================================


class TestResolverServiceRebuild:
    """rebuild メソッドのテスト（外部入力からの完全置換）"""

    @pytest.mark.unit
    def test_rebuild_replaces_all(self) -> None:
        repo = FakeAliasResolverRepository(
            initial=[
                build_alias_record(slug="Old1"),
                build_alias_record(slug="Old2"),
            ]
        )
        svc = ResolverService(repo)
        new_records = [
            build_alias_record(slug="New1"),
            build_alias_record(slug="New2"),
            build_alias_record(slug="New3"),
        ]
        svc.rebuild(new_records)
        ids = [r["id"] for r in repo.load_all()]
        assert ids == ["projects/New1", "projects/New2", "projects/New3"]

    @pytest.mark.unit
    def test_rebuild_validates_each_record(self) -> None:
        """rebuild 中に不正レコードがあれば ResolverError かつ既存は変更されない"""
        original = [build_alias_record(slug="Original")]
        repo = FakeAliasResolverRepository(initial=original)
        svc = ResolverService(repo)
        bad: AliasRecord = {  # type: ignore[typeddict-item]
            "id": "no_slash",
            "canonical": "X",
            "aliases": [],
            "shard": "projects",
            "target_path": "x",
            "archive_status": "active",
        }
        with pytest.raises(ResolverError):
            svc.rebuild([build_alias_record(slug="Good"), bad])
        # ロールバック：既存を維持
        ids = [r["id"] for r in repo.load_all()]
        assert ids == ["projects/Original"]

    @pytest.mark.unit
    def test_rebuild_rejects_duplicates(self) -> None:
        repo = FakeAliasResolverRepository()
        svc = ResolverService(repo)
        with pytest.raises(ResolverError, match="duplicate"):
            svc.rebuild(
                [
                    build_alias_record(slug="A"),
                    build_alias_record(slug="A"),
                ]
            )

    @pytest.mark.unit
    def test_rebuild_with_empty_list(self) -> None:
        repo = FakeAliasResolverRepository(
            initial=[build_alias_record(slug="X")]
        )
        svc = ResolverService(repo)
        svc.rebuild([])
        assert repo.load_all() == []


# =============================================================================
# query
# =============================================================================


class TestResolverServiceQuery:
    """find / list_active 等の参照系"""

    @pytest.mark.unit
    def test_find_by_id_returns_record(self) -> None:
        rec = build_alias_record(slug="A")
        repo = FakeAliasResolverRepository(initial=[rec])
        svc = ResolverService(repo)
        result = svc.find("projects/A")
        assert result["id"] == "projects/A"

    @pytest.mark.unit
    def test_find_unknown_raises(self) -> None:
        repo = FakeAliasResolverRepository()
        svc = ResolverService(repo)
        with pytest.raises(EntityNotFoundError):
            svc.find("projects/Unknown")

    @pytest.mark.unit
    def test_list_active_excludes_non_active(self) -> None:
        """completed / removed は list_active() に含まれない"""
        repo = FakeAliasResolverRepository(
            initial=[
                build_alias_record(slug="A", archive_status="active"),
                build_alias_record(slug="B", archive_status="removed"),
                build_alias_record(slug="C", archive_status="active"),
                build_alias_record(
                    slug="D",
                    archive_status="completed",
                    target_path="archive/projects/D/_project.md",
                ),
            ]
        )
        svc = ResolverService(repo)
        active = svc.list_active()
        ids = sorted(r["id"] for r in active)
        assert ids == ["projects/A", "projects/C"]

    @pytest.mark.unit
    def test_list_completed_returns_only_completed(self) -> None:
        """list_completed() は completed のみ返す"""
        repo = FakeAliasResolverRepository(
            initial=[
                build_alias_record(slug="A", archive_status="active"),
                build_alias_record(
                    slug="B",
                    archive_status="completed",
                    target_path="archive/projects/B/_project.md",
                ),
                build_alias_record(slug="C", archive_status="removed"),
                build_alias_record(
                    slug="D",
                    archive_status="completed",
                    target_path="archive/projects/D/_project.md",
                ),
            ]
        )
        svc = ResolverService(repo)
        completed = svc.list_completed()
        ids = sorted(r["id"] for r in completed)
        assert ids == ["projects/B", "projects/D"]

    @pytest.mark.unit
    def test_list_completed_empty(self) -> None:
        """completed が存在しない場合は空リスト"""
        repo = FakeAliasResolverRepository(
            initial=[build_alias_record(slug="A", archive_status="active")]
        )
        svc = ResolverService(repo)
        assert svc.list_completed() == []


# =============================================================================
# Property-based: add → remove → add 安定性
# =============================================================================


_slug_strategy = st.text(
    alphabet=st.characters(min_codepoint=ord("A"), max_codepoint=ord("z")),
    min_size=1,
    max_size=20,
).filter(lambda s: s.isidentifier())


class TestResolverServiceProperties:
    """property-based 不変条件"""

    @pytest.mark.property
    @given(slugs=st.lists(_slug_strategy, min_size=1, max_size=5, unique=True))
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_add_then_remove_then_re_add_keeps_count(self, slugs: List[str]) -> None:
        """全 slug を add → 全 remove → 全 add しても、結果は同数（archive_status は上書き）"""
        repo = FakeAliasResolverRepository()
        svc = ResolverService(repo)
        for s in slugs:
            svc.add(build_alias_record(slug=s))
        assert len(repo.load_all()) == len(slugs)

        for s in slugs:
            svc.remove(f"projects/{s}")
        # 論理削除なのでレコード数は変わらない
        assert len(repo.load_all()) == len(slugs)
        # 全 removed
        assert all(r["archive_status"] == "removed" for r in repo.load_all())

        # 再 add は重複として失敗するはず（論理削除でも id 衝突）
        for s in slugs:
            with pytest.raises(ResolverError):
                svc.add(build_alias_record(slug=s))

    @pytest.mark.property
    @given(slugs=st.lists(_slug_strategy, min_size=1, max_size=5, unique=True))
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_rebuild_then_load_all_round_trip(self, slugs: List[str]) -> None:
        """rebuild に渡したリストと load_all の結果が順序込みで一致"""
        repo = FakeAliasResolverRepository()
        svc = ResolverService(repo)
        records = [build_alias_record(slug=s) for s in slugs]
        svc.rebuild(records)
        loaded = repo.load_all()
        assert [r["id"] for r in loaded] == [r["id"] for r in records]
