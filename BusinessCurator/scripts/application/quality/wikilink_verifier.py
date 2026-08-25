#!/usr/bin/env python3
"""
WikilinkVerifier
================

Markdown ファイル内の `[[kind/Slug]]` wikilink を resolver と突合検証するユースケース。

検証ルール:
- active record: `[[kind/Slug]]` が有効
- completed record: `[[archive/kind/Slug]]` が有効、`[[kind/Slug]]` は stale link 警告
- removed record: wikilink なし（valid target ではない）
- unknown slug: broken link

設計意図:
- ResolverService.list_active() + list_completed() のみを参照
- ファイルシステム走査は呼び出し側（CLI）で行い、本クラスは検証ロジックに集中
"""

from dataclasses import dataclass, field

from application.resolver.resolver_service import ResolverService

__all__ = ["WikilinkVerifier", "VerifyResult"]


@dataclass
class VerifyResult:
    """検証結果"""

    total_links: int = 0
    valid: int = 0
    broken: list[tuple[str, str]] = field(default_factory=list)
    stale: list[tuple[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "total_links": self.total_links,
            "valid": self.valid,
            "broken_count": len(self.broken),
            "stale_count": len(self.stale),
            "broken": [{"file": f, "link": link} for f, link in self.broken],
            "stale": [{"file": f, "link": link} for f, link in self.stale],
        }


class WikilinkVerifier:
    """wikilink 検証ユースケース"""

    def __init__(self, resolver_service: ResolverService) -> None:
        self._resolver = resolver_service
        self._active_ids: set[str] = set()
        self._completed_ids: set[str] = set()
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._active_ids = {r["id"] for r in self._resolver.list_active()}
        self._completed_ids = {r["id"] for r in self._resolver.list_completed()}
        self._loaded = True

    def verify_links(self, links: list[tuple[str, str]]) -> VerifyResult:
        """
        wikilink のリストを検証する

        Args:
            links: (source_file, wikilink_target) のリスト。
                   wikilink_target は "kind/Slug" or "archive/kind/Slug" 形式。

        Returns:
            VerifyResult
        """
        self._ensure_loaded()
        result = VerifyResult(total_links=len(links))

        for source_file, link_target in links:
            if link_target.startswith("archive/"):
                parts = link_target.split("/", 2)
                if len(parts) >= 3:
                    record_id = f"{parts[1]}/{parts[2]}"
                else:
                    result.broken.append((source_file, link_target))
                    continue

                if record_id in self._completed_ids:
                    result.valid += 1
                elif record_id in self._active_ids:
                    result.stale.append((source_file, link_target))
                else:
                    result.broken.append((source_file, link_target))
            else:
                record_id = link_target
                if record_id in self._active_ids:
                    result.valid += 1
                elif record_id in self._completed_ids:
                    result.stale.append((source_file, link_target))
                else:
                    result.broken.append((source_file, link_target))

        return result
