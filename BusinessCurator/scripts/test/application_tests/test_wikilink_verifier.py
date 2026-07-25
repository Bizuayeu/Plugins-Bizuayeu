#!/usr/bin/env python3
"""
application/quality/wikilink_verifier.py テスト
=================================================

WikilinkVerifier の検証ロジック。
"""

import pytest

from application.quality.wikilink_verifier import WikilinkVerifier
from application.resolver.resolver_service import ResolverService
from test.test_helpers import FakeAliasResolverRepository, build_alias_record


def _make_verifier(records=None):  # type: ignore[no-untyped-def]
    repo = FakeAliasResolverRepository(initial=records or [])
    svc = ResolverService(repo)
    return WikilinkVerifier(svc)


class TestWikilinkVerifier:
    @pytest.mark.unit
    def test_active_wikilink_valid(self) -> None:
        v = _make_verifier([build_alias_record(slug="A")])
        result = v.verify_links([("file.md", "projects/A")])
        assert result.valid == 1
        assert len(result.broken) == 0

    @pytest.mark.unit
    def test_completed_archive_wikilink_valid(self) -> None:
        v = _make_verifier(
            [
                build_alias_record(
                    slug="B",
                    archive_status="completed",
                    target_path="archive/projects/B/_project.md",
                )
            ]
        )
        result = v.verify_links([("file.md", "archive/projects/B")])
        assert result.valid == 1

    @pytest.mark.unit
    def test_shards_link_to_completed_is_stale(self) -> None:
        """shards/X 形式で completed を参照 → stale link 警告"""
        v = _make_verifier(
            [
                build_alias_record(
                    slug="C",
                    archive_status="completed",
                    target_path="archive/projects/C/_project.md",
                )
            ]
        )
        result = v.verify_links([("file.md", "projects/C")])
        assert len(result.stale) == 1

    @pytest.mark.unit
    def test_archive_link_to_active_is_stale(self) -> None:
        """archive/X 形式で active を参照 → stale（premature archive ref）"""
        v = _make_verifier([build_alias_record(slug="D")])
        result = v.verify_links([("file.md", "archive/projects/D")])
        assert len(result.stale) == 1

    @pytest.mark.unit
    def test_unknown_slug_is_broken(self) -> None:
        v = _make_verifier([build_alias_record(slug="A")])
        result = v.verify_links([("file.md", "projects/Unknown")])
        assert len(result.broken) == 1

    @pytest.mark.unit
    def test_removed_record_is_not_valid_target(self) -> None:
        """removed レコードへの wikilink は broken"""
        v = _make_verifier([build_alias_record(slug="E", archive_status="removed")])
        result = v.verify_links([("file.md", "projects/E")])
        assert len(result.broken) == 1

    @pytest.mark.unit
    def test_total_links_counted(self) -> None:
        v = _make_verifier([build_alias_record(slug="X")])
        result = v.verify_links(
            [
                ("a.md", "projects/X"),
                ("b.md", "projects/Missing"),
            ]
        )
        assert result.total_links == 2

    @pytest.mark.unit
    def test_to_dict_format(self) -> None:
        v = _make_verifier([build_alias_record(slug="A")])
        result = v.verify_links([("file.md", "projects/A")])
        d = result.to_dict()
        assert "total_links" in d
        assert "broken_count" in d
        assert "stale_count" in d
