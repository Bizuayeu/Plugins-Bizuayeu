---
name: wiki-triage
description: raw-entries/ 全件をルールベース triage で振り分け。alias resolver から自動生成されるルールで判定し、未マッチは LLM フォールバック (claude -p) または unclassified に保留する。
---

# /wiki-triage

raw-entries を 4 シャードに振り分けます。

## 動作

[triage.md](../skills/wiki/triage.md) スキルに委譲します。スキルが `interfaces.triage_cli` を呼び出します：

```bash
python -m interfaces.triage_cli --plugin-root <plugin_root>
```

LLM フォールバックを無効化するには `--no-llm`:

```bash
python -m interfaces.triage_cli --plugin-root <plugin_root> --no-llm
```

## JSON 出力

```json
{
  "status": "ok",
  "total": 10,
  "rule_match": 7,
  "llm_fallback": 2,
  "unclassified": 1
}
```

## 関連

- [triage.md](../skills/wiki/triage.md): ルール生成・LLM フォールバック・保留対応の詳細
- `/wiki-ingest`: 前段
- `/wiki-absorb`: 後段
