---
name: wiki-ingest
description: data/ のメールファイル（.eml/.mbox）をパースして inbox/raw-entries/ に YAML frontmatter 付き md として保存する。
---

# /wiki-ingest

メールファイルを raw-entries に取り込みます。

## 動作

`interfaces.ingest_cli` を直接呼び出します（スキル不要、純機械処理）：

```bash
python -m interfaces.ingest_cli \
  --source <path-to-eml-or-mbox> \
  --plugin-root <plugin_root>
```

## JSON 出力

```json
{
  "status": "ok",
  "saved": 5,
  "skipped": 0,
  "failed": 0,
  "total": 5
}
```

`saved` は新規取り込み数、`skipped` は既存と判断されたエントリ数（冪等性）。

## 動作詳細

1. format_detector が拡張子 + シグネチャで .eml/.mbox を判定
2. 対応するパーサで EmailMessage に変換
3. ParseEmailUseCase で RawEntry に変換
4. 既存 entry_id があれば skip、なければ `inbox/raw-entries/{id}.md` に保存

## 使用例

```text
/wiki-ingest data/2026-04-07.mbox
```

→ JSON 出力 → ユーザーに件数を報告 → 続けて `/wiki-triage` を提案

## 関連

- `/wiki-triage`: 取り込んだエントリの振り分け
- `/wiki-status`: 件数確認
