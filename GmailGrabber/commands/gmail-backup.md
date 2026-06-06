---
description: 検索クエリで Gmail メッセージを .eml / .mbox にバックアップする
---

# /gmail-backup

Gmail 検索クエリで絞り込んだメッセージを .eml (1ファイル1メール) または
.mbox (1ファイルに束ねる) 形式で指定ディレクトリに書き出します。
中断しても `--no-resume` を指定しない限り自動的に前回の続きから再開します。

## 使い方

```bash
python -m interfaces.backup_cli \
  --email <address> \
  --client-secret <path> \
  --output-dir <dir> \
  [--format eml|mbox] \
  [--after YYYY/MM/DD] [--before YYYY/MM/DD] \
  [--from-addr ADDR] [--to-addr ADDR] [--subject TEXT] \
  [--label LABEL] [--has-attachment] \
  [--raw-query "gmail query string"] \
  [--max-messages N] \
  [--no-resume]
```

## パラメータ

- `--email` (必須): 認証済みアカウント
- `--client-secret` (必須): OAuth credentials
- `--output-dir` (必須): 書き出し先ディレクトリ（自動作成）
- `--format`: `eml` (デフォルト) | `mbox`
- `--after` / `--before`: 日付範囲（Gmail仕様 YYYY/MM/DD）
- `--from-addr` / `--to-addr` / `--subject`: 絞り込み
- `--label`: Gmail ラベルで絞り込み
- `--has-attachment`: 添付ファイル付きのみ
- `--raw-query`: 生Gmail検索クエリ（他の条件を上書き）
- `--max-messages`: 取得上限
- `--no-resume`: 前回の state を無視して新規実行

## 実行例: togami-log@ の 2026年4月分を BusinessWiki に保存

```bash
cd /path/to/GmailGrabber
PYTHONPATH=scripts python -m interfaces.backup_cli \
  --email togami-log@meguru-construction.com \
  --client-secret ~/.gmailgrabber/client_secret.json \
  --output-dir '/path/to/workspace/BusinessWiki/data/2026-04' \
  --format eml \
  --after 2026/04/01 --before 2026/04/12
```

## 出力

```json
{
  "status": "ok",
  "plan_id": "plan_20260411_100030_abc12345",
  "account": "togami-log@meguru-construction.com",
  "query": "after:2026/04/01 before:2026/04/12",
  "output_dir": "/path/to/workspace/BusinessWiki/data/2026-04",
  "output_format": "eml",
  "success_count": 42,
  "failure_count": 0,
  "output_files_count": 42,
  "started_at": "2026-04-11T10:00:30+00:00",
  "finished_at": "2026-04-11T10:02:15+00:00"
}
```
