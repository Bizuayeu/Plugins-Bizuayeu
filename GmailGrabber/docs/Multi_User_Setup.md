# Multi-User Workspace Backup セットアップガイド

Google Workspace 環境で複数ユーザーの Gmail を一括バックアップするための、
Service Account + Domain-Wide Delegation (DWD) 設定手順です。

## 前提

- Google Workspace Business Standard 以上 (Super Admin 権限必要)
- Google Cloud プロジェクト (既存の GmailGrabber 用プロジェクト流用可)
- 対象ドメイン (例: `meguru-construction.com`)

## 全体の流れ

```
[1] Google Cloud Console
    → Service Account 作成
    → JSON key ダウンロード

[2] Workspace Admin Console
    → Domain-Wide Delegation 有効化
    → クライアントID + スコープを登録

[3] ローカル環境
    → JSON key を配置
    → users.txt を作成

[4] 実行
    → /gmail-multi-backup コマンド
```

## ステップ1: Google Cloud Console で Service Account 作成

### 1-A. Service Account 作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. GmailGrabber プロジェクトを選択 (既存のものがあれば流用)
3. 左メニュー **「IAM と管理」** → **「サービス アカウント」**
4. 上部 **「+ サービス アカウントを作成」**
5. 以下を入力:
   - **名前**: `gmailgrabber-workspace`
   - **ID**: (自動生成でOK)
   - **説明**: `Multi-user Gmail backup for workspace`
6. **「作成して続行」**
7. **ロール**: そのまま「続行」(Service Account 自身には特別なロール不要、DWD で user impersonation する)
8. **「完了」**

### 1-B. JSON key のダウンロード

1. 作成した Service Account の行をクリック
2. 上部タブ **「キー」**
3. **「キーを追加」** → **「新しい鍵を作成」**
4. キーのタイプ: **「JSON」** → **「作成」**
5. JSON ファイルが自動ダウンロード

**セキュリティ重要**: このファイルはドメイン全体のメールアクセス権を持つ強力な鍵です。
- git にコミットしない (`.gitignore` に追加済み)
- 権限 600 で配置 (Unix 系)
- 必要な人以外に共有しない

### 1-C. Service Account の Client ID をメモ

サービスアカウント詳細画面で **「詳細設定を表示」** → **「一意の ID」** (数字列、例: `123456789012345678901`) をコピー。次のステップで使います。

## ステップ2: Workspace Admin Console で DWD 設定

### 2-A. Domain-Wide Delegation 登録

1. [Google Workspace Admin Console](https://admin.google.com/) にアクセス (Super Admin でログイン)
2. 左メニュー **「セキュリティ」** → **「アクセスとデータ管理」** → **「API の制御」**
3. 下部の **「ドメイン全体の委任」** セクション → **「ドメイン全体の委任を管理」**
4. **「新しく追加」**
5. 以下を入力:
   - **クライアント ID**: ステップ 1-C でコピーした一意の ID
   - **OAuth スコープ (カンマ区切り)**:
     ```
     https://www.googleapis.com/auth/gmail.readonly
     ```
6. **「承認」**

### 2-B. テストユーザーへのアクセス確認

設定反映まで数分〜10分程度かかることがあります。反映後は、Service Account が該当スコープで
ドメイン内の任意ユーザーを impersonate できるようになります。

## ステップ3: ローカル環境の準備

### 3-A. JSON key の配置

Windows:
```bash
mkdir -p "$APPDATA/GmailGrabber"
mv ~/Downloads/gmailgrabber-workspace-*.json "$APPDATA/GmailGrabber/sa_key.json"
```

Unix:
```bash
mkdir -p ~/.config/gmailgrabber
mv ~/Downloads/gmailgrabber-workspace-*.json ~/.config/gmailgrabber/sa_key.json
chmod 600 ~/.config/gmailgrabber/sa_key.json
```

### 3-B. users.txt 作成

対象ユーザーを1行1email で列挙:

```
# Windows: %APPDATA%/GmailGrabber/users.txt
# Unix:    ~/.config/gmailgrabber/users.txt

alice@meguru-construction.com
bob@meguru-construction.com
carol@meguru-construction.com
# 行頭 # でコメント行
daisuke@meguru-construction.com
...
```

## ステップ4: バックアップ実行

### 4-A. 小規模ドライラン (推奨)

まず1ユーザー + 5件だけ取得して疎通確認:

```bash
cd /path/to/plugins-bizuayeu/GmailGrabber
PYTHONPATH=scripts python -m interfaces.multi_backup_cli \
  --service-account-key "$APPDATA/GmailGrabber/sa_key.json" \
  --impersonate-users "alice@meguru-construction.com" \
  --output-dir '/tmp/gmailgrabber-dryrun' \
  --format eml \
  --max-messages-per-user 5
```

成功すれば JSON 出力で `"status": "ok"` と `per_user_success` が表示されます。

### 4-B. 本番バックアップ

```bash
PYTHONPATH=scripts python -m interfaces.multi_backup_cli \
  --service-account-key "$APPDATA/GmailGrabber/sa_key.json" \
  --impersonate-users-file "$APPDATA/GmailGrabber/users.txt" \
  --output-dir 'C:/Users/anyth/DEV/homunculus/Weave/BusinessWiki/data/2026-04' \
  --format eml \
  --after 2026/04/01 --before 2026/04/12
```

## トラブルシューティング

### `unauthorized_client` エラー

Workspace Admin Console で DWD が正しく設定されていません:
- クライアント ID が Service Account の一意 ID と一致しているか確認
- スコープが正確か (末尾スペースや typo なし)
- 設定反映まで10分ほど待つ

### `invalid_grant: Invalid JWT` エラー

JSON key の `private_key` が壊れている可能性:
- 再ダウンロードして配置し直す
- ファイル末尾に余分な改行が無いか確認

### `access_denied` エラー

指定 user が存在しない or スコープが不十分:
- user email の typo 確認
- スコープに `gmail.readonly` が含まれているか確認
- スコープ変更後は再度「承認」が必要

### 一部ユーザーだけ失敗

`per_user_failure` に記録されて処理は継続します。実行後にそのユーザーだけ再実行:

```bash
PYTHONPATH=scripts python -m interfaces.multi_backup_cli \
  --service-account-key "$APPDATA/GmailGrabber/sa_key.json" \
  --impersonate-users "failed-user@meguru-construction.com" \
  --output-dir '/path/to/same/output' \
  --after 2026/04/01 --before 2026/04/12
```

再開機構により既取得分はスキップされ、未取得分のみが追加されます。

## BusinessWiki との連携

バックアップ完了後、BusinessCurator の `/wiki-ingest` で raw-entries/ に流し込めます:

```bash
cd C:/Users/anyth/.claude/plugins/cache/plugins-bizuayeu/BusinessCurator/1.0.0/scripts
python -m interfaces.ingest_cli \
  --plugin-root 'C:/Users/anyth/DEV/homunculus/Weave/BusinessWiki' \
  --source 'C:/Users/anyth/DEV/homunculus/Weave/BusinessWiki/data/2026-04'
```

その後 `/wiki-triage` → `/wiki-absorb projects` で 4シャード wiki に編み込みます。
