---
name: wiki-verify-links
description: shards/ 配下の wikilink を resolver と突合検証する。broken / stale link を検出。
---

# /wiki-verify-links

BusinessWiki の shards/ および archive/ 配下の Markdown ファイルから `[[kind/Slug]]` 形式の wikilink を抽出し、resolver の登録状態と突合検証します。

## 動作

`interfaces.quality_cli` を呼び出します：

```bash
python -m interfaces.quality_cli verify-wikilinks --plugin-root <plugin_root>
```

## 検証ルール

| wikilink 形式 | 対応 record の archive_status | 判定 |
|---|---|---|
| `[[kind/Slug]]` | active | valid |
| `[[archive/kind/Slug]]` | completed | valid |
| `[[kind/Slug]]` | completed | **stale** (archive/ 形式に更新推奨) |
| `[[archive/kind/Slug]]` | active | **stale** (premature archive ref) |
| `[[kind/Slug]]` | removed | **broken** |
| `[[kind/Slug]]` | 未登録 | **broken** |

## JSON 出力

```json
{
  "status": "ok",
  "total_links": 1306,
  "valid": 1304,
  "broken_count": 1,
  "stale_count": 1,
  "broken": [{"file": "shards/projects/X/_project.md", "link": "vendors/Unknown"}],
  "stale": [{"file": "shards/vendors/Y.md", "link": "projects/CompletedProject"}]
}
```

## ユーザーへの報告

```text
=== wikilink 検証完了 ===
Total:   1306
Valid:   1304
Broken:  1
Stale:   1

Broken links:
  shards/projects/X/_project.md → [[vendors/Unknown]]

Stale links (update recommended):
  shards/vendors/Y.md → [[projects/CompletedProject]]
    → completed project, use [[archive/projects/CompletedProject]] instead
```

## 関連

- `_alias_resolver.md` — resolver 内部管理用
- `/wiki-status` — メトリクス集計
- `/wiki-index-rebuild` — `_index.md` 再生成
