#!/usr/bin/env python3
"""
infrastructure/repositories/entry_repository.py テスト
========================================================

FileEntryRepository の I/O 動作検証。

検証ポイント:
- save: YAML frontmatter + 本文の md ファイル生成
- exists: id ベースで判定
- load: YAML frontmatter パース → RawEntry 復元
- save → load ラウンドトリップで内容一致
- 再 save で同一内容（冪等性）
- list_all: ディレクトリ内のすべてのエントリを返す
"""

import pytest

from infrastructure.repositories.entry_repository import FileEntryRepository
from test.test_helpers import build_raw_entry

# =============================================================================
# save / exists
# =============================================================================


class TestFileEntryRepositorySave:
    @pytest.fixture
    def repo(self, tmp_path):  # type: ignore[no-untyped-def]
        return FileEntryRepository(raw_entries_dir=tmp_path)

    @pytest.mark.integration
    def test_save_creates_md_file(self, tmp_path, repo: FileEntryRepository) -> None:  # type: ignore[no-untyped-def]
        entry = build_raw_entry(entry_id="email_20260407_143022_abc12345")
        repo.save(entry)
        assert (tmp_path / "email_20260407_143022_abc12345.md").exists()

    @pytest.mark.integration
    def test_save_writes_yaml_frontmatter(self, tmp_path, repo: FileEntryRepository) -> None:  # type: ignore[no-untyped-def]
        entry = build_raw_entry(subject="○○マンション排煙設備")
        repo.save(entry)
        files = list(tmp_path.glob("*.md"))
        content = files[0].read_text(encoding="utf-8")
        assert content.startswith("---\n")
        assert "subject:" in content
        assert "○○マンション排煙設備" in content

    @pytest.mark.integration
    def test_save_writes_body_after_frontmatter(self, tmp_path, repo: FileEntryRepository) -> None:  # type: ignore[no-untyped-def]
        entry = build_raw_entry(body="本文テキスト")
        repo.save(entry)
        files = list(tmp_path.glob("*.md"))
        content = files[0].read_text(encoding="utf-8")
        assert "---\n本文テキスト" in content

    @pytest.mark.integration
    def test_save_creates_dir_if_missing(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """保存先ディレクトリが存在しなくても自動作成"""
        nested = tmp_path / "a" / "b"
        repo = FileEntryRepository(raw_entries_dir=nested)
        repo.save(build_raw_entry())
        assert nested.exists()
        assert len(list(nested.glob("*.md"))) == 1


class TestFileEntryRepositoryExists:
    @pytest.mark.integration
    def test_exists_true_after_save(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        repo = FileEntryRepository(raw_entries_dir=tmp_path)
        entry = build_raw_entry(entry_id="email_20260407_143022_aaaaaaaa")
        repo.save(entry)
        assert repo.exists("email_20260407_143022_aaaaaaaa")

    @pytest.mark.integration
    def test_exists_false_when_not_saved(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        repo = FileEntryRepository(raw_entries_dir=tmp_path)
        assert not repo.exists("email_20260407_143022_zzzzzzzz")


# =============================================================================
# load / round-trip
# =============================================================================


class TestFileEntryRepositoryLoad:
    @pytest.mark.integration
    def test_round_trip(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """save → load で内容が一致"""
        repo = FileEntryRepository(raw_entries_dir=tmp_path)
        entry = build_raw_entry(
            entry_id="email_20260407_143022_abc12345",
            subject="○○マンション",
            from_addr="sender@meguru.example.jp",
            to_addrs=["a@x", "b@y"],
            cc_addrs=["c@z"],
            attachments=["排煙計算書.pdf"],
            body="本文です\n複数行も対応",
        )
        repo.save(entry)
        loaded = repo.load("email_20260407_143022_abc12345")
        assert loaded["id"] == entry["id"]
        assert loaded["subject"] == entry["subject"]
        assert loaded["from_addr"] == entry["from_addr"]
        assert loaded["to_addrs"] == entry["to_addrs"]
        assert loaded["cc_addrs"] == entry["cc_addrs"]
        assert loaded["attachments"] == entry["attachments"]
        assert loaded["body"] == entry["body"]
        assert loaded["thread_id"] == entry["thread_id"]

    @pytest.mark.integration
    def test_load_unknown_raises(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        from domain.exceptions import EntityNotFoundError

        repo = FileEntryRepository(raw_entries_dir=tmp_path)
        with pytest.raises(EntityNotFoundError):
            repo.load("email_20260101_000000_zzzzzzzz")

    @pytest.mark.integration
    def test_round_trip_with_thread_id(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        repo = FileEntryRepository(raw_entries_dir=tmp_path)
        entry = build_raw_entry(thread_id="<thread123@x>")
        repo.save(entry)
        loaded = repo.load(entry["id"])
        assert loaded["thread_id"] == "<thread123@x>"


# =============================================================================
# 冪等性
# =============================================================================


class TestFileEntryRepositoryIdempotency:
    @pytest.mark.integration
    def test_re_save_same_content(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """同一エントリ2回 save で内容同一"""
        repo = FileEntryRepository(raw_entries_dir=tmp_path)
        entry = build_raw_entry()
        repo.save(entry)
        first = (tmp_path / f"{entry['id']}.md").read_text(encoding="utf-8")
        repo.save(entry)
        second = (tmp_path / f"{entry['id']}.md").read_text(encoding="utf-8")
        assert first == second


# =============================================================================
# list_all
# =============================================================================


class TestFileEntryRepositoryListAll:
    @pytest.mark.integration
    def test_list_all_empty(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        repo = FileEntryRepository(raw_entries_dir=tmp_path)
        assert repo.list_all() == []

    @pytest.mark.integration
    def test_list_all_returns_all_entries(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        repo = FileEntryRepository(raw_entries_dir=tmp_path)
        ids = [
            "email_20260407_143022_aaaaaaaa",
            "email_20260407_143023_bbbbbbbb",
            "email_20260407_143024_cccccccc",
        ]
        for eid in ids:
            repo.save(build_raw_entry(entry_id=eid))
        all_entries = repo.list_all()
        assert sorted(e["id"] for e in all_entries) == sorted(ids)

    @pytest.mark.integration
    def test_list_all_ignores_non_md_files(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """同一ディレクトリの .md 以外は無視"""
        repo = FileEntryRepository(raw_entries_dir=tmp_path)
        repo.save(build_raw_entry())
        (tmp_path / "junk.txt").write_text("noise")
        (tmp_path / ".hidden").write_text("hidden")
        assert len(repo.list_all()) == 1
