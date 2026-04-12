---
description: Gmail アカウントの全ラベル一覧を取得する
---

# /gmail-labels

Gmail アカウントに存在する全ラベル (system + user) を JSON で出力します。
バックアップ時のラベル指定前に、正しいラベル名を確認する用途で使用します。

## 使い方

```bash
python -m interfaces.labels_cli \
  --email <address> \
  --client-secret <path>
```

## 実行例

```bash
cd /path/to/GmailGrabber
PYTHONPATH=scripts python -m interfaces.labels_cli \
  --email togami-log@meguru-construction.com \
  --client-secret ~/.gmailgrabber/client_secret.json
```

## 出力

```json
{
  "status": "ok",
  "email": "togami-log@meguru-construction.com",
  "label_count": 24,
  "labels": [
    {"id": "INBOX", "name": "INBOX", "type": "system"},
    {"id": "Label_123", "name": "案件/高尾", "type": "user"}
  ]
}
```
