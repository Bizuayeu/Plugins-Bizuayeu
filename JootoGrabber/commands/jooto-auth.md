---
description: Jooto API key による認証を確認する
---

# /jooto-auth

`.env` に設定した `JOOTO_API_KEY` で Jooto API (`GET /v1/boards?per_page=1`) を呼び出し、認証が通ることとアクセス可能なボード総数を確認します。

## 使い方

```bash
cd /path/to/JootoGrabber
PYTHONPATH=scripts python -m interfaces.auth_cli
```

## 前提条件

1. `.env` に `JOOTO_API_KEY` を設定済み（`.env.example` をコピー）
2. API key は https://app.jooto.com の個人設定画面で発行

## 出力

成功時:
```json
{
  "status": "ok",
  "base_url": "https://app.jooto.com",
  "boards_total": 30
}
```

失敗時 (401/403):
```json
{
  "status": "error",
  "reason": "unauthorized",
  "http_status": 401
}
```
