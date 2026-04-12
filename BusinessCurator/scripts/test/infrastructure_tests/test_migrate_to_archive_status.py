#!/usr/bin/env python3
"""
infrastructure/migrations/migrate_to_archive_status.py テスト
===============================================================

v3 旧フォーマット → v4 新フォーマットの migration テスト。
"""

import pytest

from infrastructure.migrations.migrate_to_archive_status import (
    _parse_old_format,
    migrate,
)

_OLD_FORMAT = """\
# Global Index

## projects/
- [TestProject](shards/projects/TestProject/_project.md) — also: TP

## vendors/
- [ActiveVendor](shards/vendors/ActiveVendor.md) — also: av.com

## archive/ [archived]
- [old-vendor.com](shards/vendors/OldVendor.md) — also: old-vendor.com
- [Completed](archive/projects/Completed/_project.md) — also: done
"""


class TestParseOldFormat:
    @pytest.mark.unit
    def test_parses_active_and_archived(self) -> None:
        records = _parse_old_format(_OLD_FORMAT)
        assert len(records) == 4

    @pytest.mark.unit
    def test_active_records_have_active_status(self) -> None:
        records = _parse_old_format(_OLD_FORMAT)
        active = [r for r in records if r["archive_status"] == "active"]
        assert len(active) == 2

    @pytest.mark.unit
    def test_shards_target_in_old_archive_becomes_removed(self) -> None:
        records = _parse_old_format(_OLD_FORMAT)
        old_vendor = [r for r in records if r["id"] == "vendors/OldVendor"][0]
        assert old_vendor["archive_status"] == "removed"

    @pytest.mark.unit
    def test_archive_target_in_old_archive_becomes_completed(self) -> None:
        records = _parse_old_format(_OLD_FORMAT)
        completed = [r for r in records if r["id"] == "projects/Completed"][0]
        assert completed["archive_status"] == "completed"


class TestMigrate:
    @pytest.mark.integration
    def test_dry_run_does_not_modify(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        resolver = tmp_path / "_alias_resolver.md"
        resolver.write_text(_OLD_FORMAT, encoding="utf-8")
        report = migrate(tmp_path, dry_run=True)
        assert "DRY RUN" in report
        content = resolver.read_text(encoding="utf-8")
        assert "## archive/ [archived]" in content

    @pytest.mark.integration
    def test_real_run_converts_to_new_format(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        resolver = tmp_path / "_alias_resolver.md"
        resolver.write_text(_OLD_FORMAT, encoding="utf-8")
        report = migrate(tmp_path, dry_run=False)
        assert "DONE" in report
        content = resolver.read_text(encoding="utf-8")
        assert "## archive/ [archived]" not in content
        assert "## archive/vendors/ [removed]" in content
        assert "## archive/projects/ [completed]" in content

    @pytest.mark.integration
    def test_already_migrated_returns_nothing_to_do(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        resolver = tmp_path / "_alias_resolver.md"
        resolver.write_text("# Global Index\n\n## projects/\n", encoding="utf-8")
        report = migrate(tmp_path, dry_run=False)
        assert "Already migrated" in report or "No old-format" in report
