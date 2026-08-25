#!/usr/bin/env python3
"""
ArchiveOrchestrator
===================

案件アーカイブの application 層オーケストレーター。

責務（業務計画書 §3.3）:
- create_manifest: 案件 slug → ArchiveManifest を構築
- execute: ResolverService.complete_archive() で archive_status="completed" + target_path 更新
- 実ファイル移動（os.rename）は CLI 側で行う（manifest を受け取って実行）

設計意図:
- 対話 (AskUserQuestion) は md スキル側に閉じ込める
- Python は決定的な「manifest 構築 + resolver 更新」のみ
- v4: archive_status="removed" のレコードは完工アーカイブ不可（ArchiveError）
- v4: complete_archive() atomic メソッドで edit + remove の 2 段階呼びを廃止
"""


from application.resolver.resolver_service import ResolverService
from domain.exceptions import ArchiveError, EntityNotFoundError
from domain.protocols import ClockProtocol
from domain.types.archive import ArchiveManifest, ExtractedKnowledge

__all__ = ["ArchiveOrchestrator"]


_DEFAULT_REASON = "completed"


class ArchiveOrchestrator:
    """案件アーカイブのオーケストレーター"""

    def __init__(
        self,
        resolver_service: ResolverService,
        clock: ClockProtocol,
    ) -> None:
        self._resolver = resolver_service
        self._clock = clock

    # ------------------------------------------------------------------
    # create_manifest
    # ------------------------------------------------------------------

    def create_manifest(
        self,
        project_slug: str,
        *,
        reason: str = _DEFAULT_REASON,
        extracted_knowledge: list[ExtractedKnowledge] | None = None,
    ) -> ArchiveManifest:
        """
        アーカイブマニフェストを構築（resolver は更新しない）

        Args:
            project_slug: 対象案件の slug
            reason: アーカイブ理由
            extracted_knowledge: 抽出された知見記事のリスト

        Returns:
            ArchiveManifest

        Raises:
            EntityNotFoundError: 該当する projects/ レコードが存在しない
            ArchiveError: 既に completed または removed のレコードはアーカイブ不可
        """
        record_id = f"projects/{project_slug}"
        try:
            record = self._resolver.find(record_id)
        except EntityNotFoundError as e:
            raise EntityNotFoundError(f"project not found in resolver: {record_id}") from e

        if record["archive_status"] == "completed":
            raise ArchiveError(f"project already archived: {record_id}")
        if record["archive_status"] == "removed":
            raise ArchiveError(
                f"cannot archive removed record: {record_id} "
                f"(removed records are logically deleted, not archivable)"
            )

        return {
            "project_slug": project_slug,
            "project_canonical": record["canonical"],
            "archived_at": self._clock.now().isoformat(),
            "reason": reason,
            "source_path": f"shards/projects/{project_slug}",
            "destination_path": f"archive/projects/{project_slug}",
            "extracted_knowledge": list(extracted_knowledge or []),
        }

    # ------------------------------------------------------------------
    # execute
    # ------------------------------------------------------------------

    def execute(
        self,
        project_slug: str,
        *,
        reason: str = _DEFAULT_REASON,
        extracted_knowledge: list[ExtractedKnowledge] | None = None,
    ) -> ArchiveManifest:
        """
        manifest 生成 + resolver 更新（archive_status="completed", target_path → archive/）

        Args:
            project_slug: 対象案件 slug
            reason: アーカイブ理由
            extracted_knowledge: 抽出知見

        Returns:
            ArchiveManifest

        Raises:
            EntityNotFoundError: 案件未登録
            ArchiveError: 既に completed / removed 状態のレコード
        """
        manifest = self.create_manifest(
            project_slug,
            reason=reason,
            extracted_knowledge=extracted_knowledge,
        )

        record_id = f"projects/{project_slug}"
        new_target = f"{manifest['destination_path']}/_project.md"
        self._resolver.complete_archive(record_id, new_target_path=new_target)

        return manifest
