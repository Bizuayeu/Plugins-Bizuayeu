---
description: Jooto ボード（単一 or 全アクティブ）のタスク/リスト/カテゴリを JSON に保存する
---

# /jooto-backup

指定ボード（または全アクティブボード）から `tasks` / `lists` / `categories` を取得し、`data/jooto/{id}_{title}/` 配下に JSON として保存します。BusinessCurator の吸収元となるファイル。

## 使い方

```bash
# 単一ボード
PYTHONPATH=scripts python -m interfaces.backup_cli --board 1287379

# 全アクティブボード（archived=false のみ）
PYTHONPATH=scripts python -m interfaces.backup_cli --all-active

# 出力先を上書き
PYTHONPATH=scripts python -m interfaces.backup_cli --all-active --output /tmp/jooto
```

## 出力レイアウト

```
data/jooto/
└── 1287379_FY26_18_東長崎4丁目/
    ├── board.json        ← board 本体
    ├── tasks.json        ← タスク配列
    ├── lists.json        ← リスト（列）配列
    └── categories.json   ← ラベル配列
```

## 出力例

```json
{
  "status": "ok",
  "boards_backed_up": 1,
  "results": [
    {"board_id": 1287379, "title": "FY26_18 東長崎4丁目", "tasks_count": 42, "lists_count": 4, "categories_count": 6, "path": "data/jooto/1287379_FY26_18_東長崎4丁目"}
  ]
}
```

## 注意

- `data/` は `.gitignore` 済み（機密性があるため）
- 約30〜40 ボード × 3 エンドポイント = 100〜200 req/回。GET レート制限 600/分の範囲内。
- アーカイブ済みボード取得は `--board <id>` で個別指定のみ（`--all-active` は対象外）
