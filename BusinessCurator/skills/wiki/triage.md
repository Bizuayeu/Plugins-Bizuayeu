---
name: triage
description: メール振り分け運用スキル。triage_cli を呼び出してルールベース判定を実行し、未分類エントリを LLM フォールバックまたは AskUserQuestion で解決する。
---

# triage

raw-entries/ のエントリを 4 シャードに振り分ける運用スキルです。

## 振り分けロジック

1. **ルールベース**（80%目標）: alias resolver の canonical / aliases から自動生成された正規表現で subject マッチ
2. **LLM フォールバック**（20%目標）: ルール未マッチ時に Claude CLI (`claude -p`) で分類
3. **保留**: それも判定不能なら `inbox/unclassified/` に保留してユーザー確認

## CLI 呼び出し

すべて `interfaces.triage_cli` 経由。

### デフォルト実行（LLM フォールバック有効）

```bash
python -m interfaces.triage_cli --plugin-root <plugin_root>
```

### LLM スキップ（オフライン / CI / デバッグ）

```bash
python -m interfaces.triage_cli --plugin-root <plugin_root> --no-llm
```

`--no-llm` モードはルール未マッチエントリを `unclassified` のまま残します。

## JSON 出力スキーマ

```json
{
  "status": "ok",
  "total": 10,
  "rule_match": 7,
  "llm_fallback": 2,
  "unclassified": 1
}
```

各カウントの意味:
- `rule_match`: ルールベースで決着
- `llm_fallback`: LLM 判定で決着
- `unclassified`: 判定不能（要ユーザー対応）

## 実行フロー

1. `python -m interfaces.triage_cli --plugin-root <plugin_root>` を Bash で実行
2. JSON 出力を解析
3. ユーザーに結果を整形して報告（rule_match / llm_fallback / unclassified の割合）
4. `unclassified > 0` なら：
   - `inbox/unclassified/` の中身を一覧表示
   - 各エントリについて AskUserQuestion で「どのシャードに振り分けますか？」
   - 回答に応じて resolver にエイリアスを追加（次回からルールマッチするように）

## ルール管理

triage_cli は実行のたびに alias resolver からルールを再生成するので、**ルールファイルを直接編集する必要はありません**。

新しいパターンを追加したい場合：
- 物件識別子なら `project-manager.md` で edit → `--add-aliases`
- ドメインなら `client-manager.md` または `vendor-manager.md` で edit
- 知見キーワードなら `knowledge-manager.md` で edit

## 監査ログ

triage の判定履歴は `triage_logs/_triage_log_YYYYMMDD.json` に追記されます。

各エントリのフォーマット:
```json
{
  "timestamp": "2026-04-07T14:35:00+09:00",
  "decision": {
    "entry_id": "email_20260407_143022_abc12345",
    "primary_shard": "projects",
    "primary_slug": "MaruMaru",
    "secondary_tags": ["clients/Shikaku"],
    "confidence": "rule_match",
    "matched_rules": ["○○マンション"]
  },
  "llm_invoked": false
}
```

## エラー対応

- alias resolver が空 → manager 系コマンドでマスタデータを登録するよう案内
- LLM CLI failure → `--no-llm` での再実行を提案
- raw-entries/ が空 → `/wiki-ingest` の実行を案内
