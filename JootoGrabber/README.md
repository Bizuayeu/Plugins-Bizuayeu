# JootoGrabber

Jooto API からボード/タスクを取得し、BusinessCurator が吸収可能な JSON として出力する Claude Code プラグイン。

- 認証: API Key（ヘッダ `X-Jooto-Api-Key`）
- Base URL: `https://app.jooto.com`
- 設計: Clean Architecture + TDD（[DEV.md](../DEV.md) 参照）
- 実装計画: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)

## Status

**Stage 1: Auth & Client Foundation** — 実装中

## Setup

```bash
cp .env.example .env
# .env の JOOTO_API_KEY を編集
```

## Commands

- `/jooto-auth` — API key で `/organizations` を叩き、認証成功を確認

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```
