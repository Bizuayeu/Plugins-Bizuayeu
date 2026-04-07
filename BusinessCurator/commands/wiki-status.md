---
name: wiki-status
description: シャード横断のメトリクス集計（raw_entries / alias_records / unclassified 等）を JSON で出力する。
---

# /wiki-status

BusinessCurator のステータスを表示します。

## 動作

`interfaces.status_cli` を直接呼び出します（純機械処理）：

```bash
python -m interfaces.status_cli --plugin-root <plugin_root>
```

## JSON 出力

```json
{
  "status": "ok",
  "metrics": {
    "raw_entries_count": 42,
    "alias_records_total": 28,
    "alias_records_active": 25,
    "alias_records_archived": 3,
    "alias_per_shard": {
      "projects": 12,
      "clients": 8,
      "vendors": 4,
      "knowledge": 1
    },
    "unclassified_count": 5
  }
}
```

## ユーザーへの報告

JSON を解析し、テーブル形式で人間に整形して報告：

```text
=== BusinessCurator Status ===
raw entries:    42
unclassified:   5  ⚠️  triage 推奨

resolver records:
  projects:    12 (active)
  clients:      8 (active)
  vendors:      4 (active)
  knowledge:    1 (active)
  archived:     3
```

## 関連

- `/wiki-ingest`, `/wiki-triage`, `/wiki-absorb`: 状態を変える操作
