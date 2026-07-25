#!/usr/bin/env python3
"""
IndexMarkdownFormatter
======================

IndexEntry を EpisodicWiki 形式の Markdown に変換する。

設計意図:
- 出力先の書き込みは infrastructure 層に分離し、ここは純粋な文字列生成のみ。
- projects / knowledge はディレクトリ形式 ({slug}/{file}.md)、
  vendors / clients は単ファイル形式 ({slug}.md)。
- 末尾に「自動生成」フッタを付与し、手動編集への抑止メッセージを含める。
- 並び順は呼び出し側（application 層）が決定する。本クラスはソートしない。
"""

from typing import Dict, List

from domain.indexing.index_entry import IndexEntry
from domain.types.shard import SHARD_KINDS, ShardKind

__all__ = ["IndexMarkdownFormatter"]


_SHARD_LINK_STYLE = {
    "projects": "directory",
    "knowledge": "directory",
    "vendors": "file",
    "clients": "file",
}

_SHARD_DIRECTORY_INDEX_FILE = {
    "projects": "_project.md",
    "knowledge": "_index.md",
}

_AUTO_GEN_FOOTER = (
    "\n---\n\n**自動生成**: `/wiki-index-rebuild` で再生成されます。手動編集しないでください。\n"
)


class IndexMarkdownFormatter:
    """IndexEntry 群を Markdown 文字列に整形する"""

    def format_root(self, grouped: Dict[str, List[IndexEntry]]) -> str:
        """
        ルート _index.md の本文を生成

        Args:
            grouped: `{shard: [IndexEntry, ...]}` 辞書（件数のみ参照）

        Returns:
            Markdown 文字列
        """
        lines: List[str] = [
            "# BusinessWiki Index",
            "",
            "BusinessCurator で管理する 4 シャードの日本語インデックスです。",
            "各シャードの詳細は下記リンクから辿ってください。",
            "",
        ]
        for kind in SHARD_KINDS:
            count = len(grouped.get(kind, []))
            lines.append(f"- [{kind}/](shards/{kind}/_index.md) — {count}件")
        return "\n".join(lines) + _AUTO_GEN_FOOTER

    def format_shard(self, kind: ShardKind, entries: List[IndexEntry]) -> str:
        """
        シャード別 _index.md の本文を生成

        Args:
            kind: シャード種別
            entries: 並び順が確定した IndexEntry 群

        Returns:
            Markdown 文字列
        """
        lines: List[str] = [f"# {kind.capitalize()} Index", ""]

        if not entries:
            lines.append("*(まだマスタが登録されていません)*")
        else:
            for entry in entries:
                relative_link = self._shard_relative_link(kind, entry)
                line = f"- [{entry.canonical}]({relative_link})"
                if entry.aliases:
                    line += f" — also: {', '.join(entry.aliases)}"
                lines.append(line)

        return "\n".join(lines) + _AUTO_GEN_FOOTER

    # ------------------------------------------------------------------
    # private
    # ------------------------------------------------------------------

    def _shard_relative_link(self, kind: ShardKind, entry: IndexEntry) -> str:
        """
        シャードディレクトリからの相対リンクを組み立てる。

        projects: `{slug}/_project.md`
        knowledge: `{slug}/_index.md`
        vendors / clients: `{slug}.md`
        """
        style = _SHARD_LINK_STYLE[kind]
        if style == "directory":
            index_file = _SHARD_DIRECTORY_INDEX_FILE[kind]
            return f"{entry.slug}/{index_file}"
        return f"{entry.slug}.md"
