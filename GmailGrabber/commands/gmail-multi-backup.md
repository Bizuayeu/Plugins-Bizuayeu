---
description: Service Account + DWD で Workspace 複数ユーザーの Gmail を一括バックアップ、Message-ID で重複排除
---

# /gmail-multi-backup

Google Workspace 環境で Service Account + Domain-Wide Delegation を使い、
複数ユーザー (30人等) の Gmail を一括取得します。
CC配信で同じメールが複数受信箱にあっても、RFC5322 Message-ID で重複排除し、
1メール1ファイルで出力します。

## 使い方

```bash
PYTHONPATH=scripts python -m interfaces.multi_backup_cli \
  --service-account-key <PATH> \
  (--impersonate-users a@d.com,b@d.com | --impersonate-users-file users.txt) \
  --output-dir <DIR> \
  [--format eml|mbox] \
  [--after YYYY/MM/DD] [--before YYYY/MM/DD] \
  [--from-addr ADDR] [--subject TEXT] [--label NAME] \
  [--has-attachment] [--raw-query "q"] \
  [--max-messages-per-user N] \
  [--no-resume]
```

## パラメータ

- `--service-account-key` (必須): Google Cloud で作成した Service Account JSON key
- `--impersonate-users` / `--impersonate-users-file` (どちらか必須): 対象ユーザーリスト
- `--output-dir` (必須): 書き出し先
- `--format`: `eml` (デフォルト) | `mbox`
- `--after` / `--before`: 日付範囲
- 他: `--from-addr`, `--to-addr`, `--subject`, `--label`, `--has-attachment`, `--raw-query`
- `--max-messages-per-user`: 各ユーザーごとの取得上限
- `--no-resume`: 前回の state を無視して新規実行

## 前提条件

1. Google Workspace Admin 権限
2. Google Cloud プロジェクトで Service Account 作成
3. Workspace Admin Console で Domain-Wide Delegation 設定済み
4. スコープ: `https://www.googleapis.com/auth/gmail.readonly`

詳細は [docs/Multi_User_Setup.md](../docs/Multi_User_Setup.md) 参照。

## 実行例: めぐる組 30人分の4月バックアップ

```bash
PYTHONPATH=scripts python -m interfaces.multi_backup_cli \
  --service-account-key "$APPDATA/GmailGrabber/sa_key.json" \
  --impersonate-users-file "$APPDATA/GmailGrabber/users.txt" \
  --output-dir '/path/to/workspace/BusinessWiki/data/2026-04' \
  --format eml \
  --after 2026/04/01 --before 2026/04/12
```

## 出力例

```json
{
  "status": "ok",
  "multi_plan_id": "multi_plan_20260411_100030_abc12345ef",
  "user_count": 30,
  "query": "after:2026/04/01 before:2026/04/12",
  "output_dir": "/path/to/workspace/BusinessWiki/data/2026-04",
  "output_format": "eml",
  "per_user_success": {"user1@meguru.example.jp": 50, "user2@meguru.example.jp": 12, ...},
  "per_user_deduped": {"user1@meguru.example.jp": 0, "user2@meguru.example.jp": 38, ...},
  "total_unique_messages": 850,
  "total_dedup_skipped": 340,
  "total_messages_without_message_id": 2
}
```

## 中断・再開

- デフォルトで `~/.config/gmailgrabber/multi_state/` に進行状態が保存される
- 同じコマンド再実行 → 完了済みユーザーはスキップ、未完了ユーザーの未取得分を追加取得
- `message_id_index` は全 plan で継続するため、再開時も dedup が効く
- 完全にやり直したい場合は `--no-resume`

## 重複排除の動作

同じメール (同じ Message-ID) が複数ユーザーの受信箱にある場合:
1. 最初に遭遇したユーザーの版を書き込み + `message_id_index` に登録
2. 後続ユーザーで同じ Message-ID を検出 → 書き込みスキップ、`per_user_deduped` にカウント

Message-ID ヘッダが欠落しているメール (spam等) は:
- dedup 対象外
- 全ユーザー分強制書き込み
- `total_messages_without_message_id` にカウント + stderr に警告ログ
