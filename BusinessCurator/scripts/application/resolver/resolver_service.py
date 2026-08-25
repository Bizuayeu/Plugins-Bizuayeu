#!/usr/bin/env python3
"""
ResolverService
===============

エイリアスリゾルバ CRUD ユースケース。

設計意図:
- AliasResolverRepositoryProtocol に依存（infrastructure 非依存）
- 全操作後に save_all で永続化（明示的な write-through）
- add/edit/remove/complete_archive/rebuild/find/list_active/list_completed を提供
- 例外: 重複 ID → ResolverError, 未登録 ID → EntityNotFoundError
- 業務計画書 §4.3, §4.4 に基づく
- v4: archive_status enum 化（active/completed/removed の 3 状態）
"""

from collections.abc import Sequence

from domain.exceptions import EntityNotFoundError, ResolverError
from domain.protocols import AliasResolverRepositoryProtocol
from domain.types.alias import AliasRecord
from domain.validation import ValidationError, validate_alias_record

__all__ = ["ResolverService"]


class ResolverService:
    """エイリアスリゾルバの CRUD と検索を提供するユースケース"""

    def __init__(self, repository: AliasResolverRepositoryProtocol) -> None:
        self._repo = repository

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _safe_validate(self, record: AliasRecord) -> None:
        """ValidationError を ResolverError に変換"""
        try:
            validate_alias_record(record)
        except ValidationError as e:
            raise ResolverError(f"invalid alias record: {e}") from e

    def _find_index(self, records: list[AliasRecord], record_id: str) -> int:
        """ID から index を逆引き。見つからなければ -1"""
        for i, r in enumerate(records):
            if r["id"] == record_id:
                return i
        return -1

    # ------------------------------------------------------------------
    # add
    # ------------------------------------------------------------------

    def add(self, record: AliasRecord) -> None:
        """
        新規レコードを追加

        Args:
            record: 追加対象

        Raises:
            ResolverError: バリデーション失敗、または重複 ID
        """
        self._safe_validate(record)
        records = self._repo.load_all()
        if self._find_index(records, record["id"]) >= 0:
            raise ResolverError(f"duplicate id: {record['id']}")
        records.append(record)
        self._repo.save_all(records)

    # ------------------------------------------------------------------
    # edit
    # ------------------------------------------------------------------

    def edit(
        self,
        record_id: str,
        *,
        canonical: str | None = None,
        add_aliases: Sequence[str] | None = None,
        remove_aliases: Sequence[str] | None = None,
        target_path: str | None = None,
    ) -> None:
        """
        既存レコードを部分更新

        Args:
            record_id: 対象 ID
            canonical: 新しい正式名称（省略時は変更なし）
            add_aliases: 追加する alias（既存にマージ、重複除外）
            remove_aliases: 削除する alias
            target_path: 新しいリンク先

        Raises:
            EntityNotFoundError: ID が存在しない
            ResolverError: 更新後のレコードがバリデーション失敗
        """
        records = self._repo.load_all()
        idx = self._find_index(records, record_id)
        if idx < 0:
            raise EntityNotFoundError(f"alias record not found: {record_id}")

        existing = records[idx]

        new_aliases = list(existing["aliases"])
        if add_aliases:
            for a in add_aliases:
                if a not in new_aliases:
                    new_aliases.append(a)
        if remove_aliases:
            new_aliases = [a for a in new_aliases if a not in remove_aliases]

        updated: AliasRecord = {
            "id": existing["id"],
            "canonical": canonical if canonical is not None else existing["canonical"],
            "aliases": new_aliases,
            "shard": existing["shard"],
            "target_path": target_path if target_path is not None else existing["target_path"],
            "archive_status": existing["archive_status"],
        }

        self._safe_validate(updated)
        records[idx] = updated
        self._repo.save_all(records)

    # ------------------------------------------------------------------
    # remove (論理削除)
    # ------------------------------------------------------------------

    def remove(self, record_id: str) -> None:
        """
        論理削除（archive_status = "removed"）

        Args:
            record_id: 対象 ID

        Raises:
            EntityNotFoundError: ID が存在しない

        Note:
            既に archive_status = "removed" でも noop で成功（idempotent）。
            target_path は shards/... のまま保持（完工アーカイブではない）。
        """
        records = self._repo.load_all()
        idx = self._find_index(records, record_id)
        if idx < 0:
            raise EntityNotFoundError(f"alias record not found: {record_id}")

        existing = records[idx]
        updated: AliasRecord = {
            "id": existing["id"],
            "canonical": existing["canonical"],
            "aliases": list(existing["aliases"]),
            "shard": existing["shard"],
            "target_path": existing["target_path"],
            "archive_status": "removed",
        }
        records[idx] = updated
        self._repo.save_all(records)

    # ------------------------------------------------------------------
    # complete_archive (完工アーカイブ、v4 新規)
    # ------------------------------------------------------------------

    def complete_archive(
        self,
        record_id: str,
        *,
        new_target_path: str,
    ) -> None:
        """
        完工アーカイブ（archive_status = "completed"、target_path を archive/ 配下に更新）

        Args:
            record_id: 対象 ID
            new_target_path: 新しい target_path（archive/<kind>/X/... 配下）

        Raises:
            EntityNotFoundError: ID が存在しない
            ResolverError: バリデーション失敗（target_path 接頭辞の不整合など）

        Note:
            remove() とは意味が異なる:
              - remove: 誤登録/取引停止の論理削除（target_path 不変）
              - complete_archive: 完工した案件をアーカイブ（target_path を archive/ に移動）
            archive_orchestrator.execute() から atomic に呼ばれる。
        """
        records = self._repo.load_all()
        idx = self._find_index(records, record_id)
        if idx < 0:
            raise EntityNotFoundError(f"alias record not found: {record_id}")

        existing = records[idx]
        updated: AliasRecord = {
            "id": existing["id"],
            "canonical": existing["canonical"],
            "aliases": list(existing["aliases"]),
            "shard": existing["shard"],
            "target_path": new_target_path,
            "archive_status": "completed",
        }
        self._safe_validate(updated)
        records[idx] = updated
        self._repo.save_all(records)

    # ------------------------------------------------------------------
    # rebuild
    # ------------------------------------------------------------------

    def rebuild(self, records: Sequence[AliasRecord]) -> None:
        """
        全レコードを完全置換

        Args:
            records: 新しいレコード集合

        Raises:
            ResolverError: バリデーション失敗、または重複 ID
                （失敗時は既存リポジトリは変更されない）
        """
        new_list = list(records)

        # 全件 validate を先に済ませる（save_all 呼ばない＝ロールバック相当）
        seen_ids: set[str] = set()
        for r in new_list:
            self._safe_validate(r)
            if r["id"] in seen_ids:
                raise ResolverError(f"duplicate id in rebuild input: {r['id']}")
            seen_ids.add(r["id"])

        self._repo.save_all(new_list)

    # ------------------------------------------------------------------
    # query
    # ------------------------------------------------------------------

    def find(self, record_id: str) -> AliasRecord:
        """
        ID で検索

        Args:
            record_id: 検索対象 ID

        Returns:
            AliasRecord

        Raises:
            EntityNotFoundError: 見つからない
        """
        records = self._repo.load_all()
        idx = self._find_index(records, record_id)
        if idx < 0:
            raise EntityNotFoundError(f"alias record not found: {record_id}")
        return records[idx]

    def list_active(self) -> list[AliasRecord]:
        """
        archive_status == "active" のレコードのみを返す

        Returns:
            活性レコードのリスト（順序は load_all のまま）
        """
        return [r for r in self._repo.load_all() if r["archive_status"] == "active"]

    def list_completed(self) -> list[AliasRecord]:
        """
        archive_status == "completed" のレコードのみを返す

        Returns:
            完工アーカイブレコードのリスト（順序は load_all のまま）
        """
        return [r for r in self._repo.load_all() if r["archive_status"] == "completed"]
