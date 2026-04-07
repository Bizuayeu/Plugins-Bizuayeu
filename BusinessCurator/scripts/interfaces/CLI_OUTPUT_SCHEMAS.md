# CLI Output Schemas

すべての CLI は **JSON-only 出力** を行います（md スキルから安定的にパース可能）。

エラー時は exit code 1 + 以下の共通エラースキーマで応答します:

```json
{
  "status": "error",
  "error": "<message>",
  "details": { ... optional ... }
}
```

成功時は exit code 0 + サブコマンドごとのスキーマで応答します。

---

## ingest_cli

```bash
python -m interfaces.ingest_cli --source <path> --plugin-root <path>
```

### 成功

```json
{
  "status": "ok",
  "saved": 5,
  "skipped": 2,
  "failed": 0,
  "total": 7
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `saved` | int | 新規書き込みされたエントリ数 |
| `skipped` | int | 既存と判断され skip された件数 |
| `failed` | int | 保存失敗件数 |
| `total` | int | 入力メッセージ総数 |

### 失敗ケース

- source 不存在 / format 検出失敗 / parse error → exit 1

---

## resolver_cli

```bash
python -m interfaces.resolver_cli {add,edit,remove,list,find} ...
```

### add / edit / remove

```json
{
  "status": "ok",
  "action": "add",
  "id": "projects/MaruMaru"
}
```

### list

```json
{
  "status": "ok",
  "count": 3,
  "records": [
    {
      "id": "projects/MaruMaru",
      "canonical": "○○マンション新築工事",
      "aliases": ["○○MS", "2026-003"],
      "shard": "projects",
      "target_path": "shards/projects/MaruMaru/_project.md",
      "archived": false
    }
  ]
}
```

オプション:
- `--include-archived`: archived = True も含める
- `--shard <kind>`: 指定シャードのみ

### find

```json
{
  "status": "ok",
  "record": {
    "id": "projects/MaruMaru",
    "canonical": "○○マンション新築工事",
    ...
  }
}
```

### 失敗ケース

- duplicate id → exit 1
- not found → exit 1
- invalid alias record → exit 1

---

## triage_cli

```bash
python -m interfaces.triage_cli --plugin-root <path> [--no-llm]
```

ルールは alias resolver のアクティブレコード（canonical / aliases）から自動生成されます。
`--no-llm` 指定時は LLM フォールバックをスキップし、ルール未マッチは unclassified のままになります。

### 成功

```json
{
  "status": "ok",
  "total": 10,
  "rule_match": 7,
  "llm_fallback": 2,
  "unclassified": 1
}
```

| フィールド | 説明 |
|---|---|
| `total` | 処理した raw entry 数 |
| `rule_match` | ルールベースで決着した数 |
| `llm_fallback` | LLM フォールバックで決着した数 |
| `unclassified` | 分類できなかった数 |

### 失敗ケース

- 不正な regex（理論上発生しない: re.escape 経由）→ exit 1
- LLM CLI 失敗 → exit 1

---

## status_cli

```bash
python -m interfaces.status_cli --plugin-root <path>
```

### 成功

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

`alias_per_shard` はアクティブレコードのみカウント。

---

## archive_cli

```bash
python -m interfaces.archive_cli {plan,execute} --plugin-root <path> --project <slug> [--reason <reason>]
```

### plan（manifest 生成のみ、副作用なし）

```json
{
  "status": "ok",
  "action": "plan",
  "manifest": {
    "project_slug": "MaruMaru",
    "project_canonical": "○○マンション",
    "archived_at": "2026-04-07T15:00:00+00:00",
    "reason": "completed",
    "source_path": "shards/projects/MaruMaru",
    "destination_path": "archive/projects/MaruMaru",
    "extracted_knowledge": []
  }
}
```

### execute（resolver 更新 + ファイル移動）

```json
{
  "status": "ok",
  "action": "execute",
  "manifest": { ... },
  "moved": true
}
```

オプション:
- `--no-move`: ファイル移動をスキップ（resolver 更新のみ）
- `--reason <reason>`: アーカイブ理由（デフォルト: `completed`）

### 失敗ケース

- 案件未登録 → exit 1
- 既にアーカイブ済み → exit 1
- 移動先ディレクトリ既存 → exit 1
- 移動元ディレクトリ不存在（`--no-move` なしの場合）→ exit 1
