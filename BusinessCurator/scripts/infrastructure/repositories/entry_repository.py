#!/usr/bin/env python3
"""
FileEntryRepository
===================

EntryRepositoryProtocol のファイルシステム実装。

設計意図:
- 1エントリ = 1 .md ファイル（{id}.md）
- YAML frontmatter 形式で永続化
- pyyaml 依存を避けるため、自前の最小 YAML シリアライザを用いる
  （RawEntry の型のみサポート: str / list[str] / None）
- 冪等性: 同じ entry なら同じ内容を生成（list 順序は保持）
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from domain.exceptions import EntityNotFoundError
from domain.types.entry import RawEntry

__all__ = ["FileEntryRepository"]


# =============================================================================
# 自前 YAML シリアライザ（RawEntry 専用最小実装）
# =============================================================================


def _yaml_escape_string(value: str) -> str:
    """
    YAML 文字列の安全なエンコード

    特殊文字を含む場合は double-quote、それ以外はそのまま。
    Unicode 日本語は問題なくそのまま出力可能。
    """
    needs_quote = (
        value == ""
        or value.startswith(("-", ":", "?", "[", "]", "{", "}", "&", "*", "!", "|", ">", "%", "@", "`", "#"))
        or value.startswith(" ")
        or value.endswith(" ")
        or any(c in value for c in (":", "\n", "\t", "\r", '"', "'", "\\"))
    )
    if not needs_quote:
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _yaml_dump_list(items: List[str]) -> str:
    """list[str] を YAML inline list に"""
    if not items:
        return "[]"
    parts = [_yaml_escape_string(s) for s in items]
    return "[" + ", ".join(parts) + "]"


def _serialize_entry_to_yaml(entry: RawEntry) -> str:
    """
    RawEntry を YAML frontmatter 部分に直列化

    Returns:
        "---\\n<key: value>\\n...\\n---" 形式の文字列
    """
    lines: List[str] = ["---"]
    # 順序固定（再現性のため）
    lines.append(f"id: {_yaml_escape_string(entry['id'])}")
    lines.append(f"date: {_yaml_escape_string(entry['date'])}")
    lines.append(f"time: {_yaml_escape_string(entry['time'])}")
    lines.append(f"source_type: {_yaml_escape_string(entry['source_type'])}")
    lines.append(f"from_addr: {_yaml_escape_string(entry['from_addr'])}")
    lines.append(f"to_addrs: {_yaml_dump_list(entry['to_addrs'])}")
    lines.append(f"cc_addrs: {_yaml_dump_list(entry['cc_addrs'])}")
    lines.append(f"subject: {_yaml_escape_string(entry['subject'])}")
    if entry["thread_id"] is None:
        lines.append("thread_id: null")
    else:
        lines.append(f"thread_id: {_yaml_escape_string(entry['thread_id'])}")
    lines.append(f"attachments: {_yaml_dump_list(entry['attachments'])}")
    lines.append(f"tags: {_yaml_dump_list(entry['tags'])}")
    lines.append("---")
    return "\n".join(lines)


# =============================================================================
# YAML パーサ（最小実装）
# =============================================================================


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


def _yaml_unescape_string(value: str) -> str:
    """YAML quoted string → 元の文字列"""
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        inner = value[1:-1]
        return inner.replace('\\"', '"').replace("\\\\", "\\")
    return value


def _parse_yaml_list(value: str) -> List[str]:
    """inline list "[a, b, c]" → ["a", "b", "c"]"""
    value = value.strip()
    if value == "[]":
        return []
    if not (value.startswith("[") and value.endswith("]")):
        raise ValueError(f"invalid list literal: {value!r}")
    inner = value[1:-1]
    if not inner.strip():
        return []
    # naive split: 文字列内 , を考慮するため簡易ステートマシン
    parts: List[str] = []
    buf: List[str] = []
    in_string = False
    escape = False
    for ch in inner:
        if escape:
            buf.append(ch)
            escape = False
            continue
        if ch == "\\":
            buf.append(ch)
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            buf.append(ch)
            continue
        if ch == "," and not in_string:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    parts.append("".join(buf))
    return [_yaml_unescape_string(p) for p in parts]


def _parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    md 文字列を frontmatter dict + 本文 に分解

    Returns:
        (frontmatter_dict, body_text)

    Raises:
        ValueError: frontmatter フォーマット不正
    """
    m = _FRONTMATTER_RE.match(content)
    if not m:
        raise ValueError("invalid frontmatter format")
    yaml_part = m.group(1)
    body = m.group(2)

    fm: Dict[str, Any] = {}
    for line in yaml_part.split("\n"):
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid yaml line: {line!r}")
        key, _, raw_value = line.partition(":")
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value == "null":
            fm[key] = None
        elif raw_value.startswith("["):
            fm[key] = _parse_yaml_list(raw_value)
        else:
            fm[key] = _yaml_unescape_string(raw_value)
    return fm, body


# =============================================================================
# Repository
# =============================================================================


class FileEntryRepository:
    """
    raw-entries/{id}.md への永続化

    Attributes:
        _dir: 保存先ディレクトリ
    """

    def __init__(self, raw_entries_dir: Path) -> None:
        self._dir = raw_entries_dir

    def _path_for(self, entry_id: str) -> Path:
        return self._dir / f"{entry_id}.md"

    def save(self, entry: RawEntry) -> None:
        """
        エントリを {id}.md に書き出し

        Args:
            entry: 保存対象
        """
        self._dir.mkdir(parents=True, exist_ok=True)
        frontmatter = _serialize_entry_to_yaml(entry)
        body = entry["body"]
        # 本文が空でも改行は挟む（grep耐性 & 編集時のカーソル位置確保）
        content = frontmatter + "\n" + body
        target = self._path_for(entry["id"])
        target.write_text(content, encoding="utf-8")

    def exists(self, entry_id: str) -> bool:
        return self._path_for(entry_id).exists()

    def load(self, entry_id: str) -> RawEntry:
        """
        エントリを読み込み

        Args:
            entry_id: 対象 ID

        Returns:
            RawEntry

        Raises:
            EntityNotFoundError: ファイル不存在
        """
        path = self._path_for(entry_id)
        if not path.exists():
            raise EntityNotFoundError(f"entry not found: {entry_id}")

        content = path.read_text(encoding="utf-8")
        fm, body = _parse_frontmatter(content)

        return {
            "id": fm["id"],
            "date": fm["date"],
            "time": fm["time"],
            "source_type": fm["source_type"],
            "from_addr": fm["from_addr"],
            "to_addrs": fm["to_addrs"],
            "cc_addrs": fm["cc_addrs"],
            "subject": fm["subject"],
            "thread_id": fm["thread_id"],
            "attachments": fm["attachments"],
            "tags": fm["tags"],
            "body": body,
        }

    def list_all(self) -> List[RawEntry]:
        """
        ディレクトリ内のすべてのエントリを返す

        Note:
            隠しファイル/.md以外は無視
        """
        if not self._dir.exists():
            return []
        results: List[RawEntry] = []
        for path in sorted(self._dir.glob("*.md")):
            if path.name.startswith("."):
                continue
            entry_id = path.stem
            results.append(self.load(entry_id))
        return results
