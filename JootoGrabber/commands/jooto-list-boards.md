---
description: Jooto の全プロジェクト（ボード）一覧を取得する
---

# /jooto-list-boards

`/v1/boards` をページング取得し、アクセス可能なボード一覧を JSON で出力します。デフォルトでは `archived=true` のボードは除外されます。

## 使い方

```bash
cd /path/to/JootoGrabber
PYTHONPATH=scripts python -m interfaces.list_boards_cli [--include-archived]
```

## 出力例

```json
{
  "status": "ok",
  "count": 38,
  "boards": [
    {"id": 1287379, "title": "FY26_18 東長崎4丁目", "archived": false, "updated_at": "2026-04-10T12:20:58Z"}
  ]
}
```
