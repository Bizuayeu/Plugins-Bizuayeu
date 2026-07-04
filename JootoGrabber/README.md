# JootoGrabber

Jooto API からボード/タスクを取得し、BusinessCurator が吸収可能な JSON として出力する Claude Code プラグイン。

- 認証: API Key（ヘッダ `X-Jooto-Api-Key`）
- Base URL: `https://api.jooto.com`
- 設計: Clean Architecture + TDD（開発規範は [Plugins-Weave](https://github.com/Bizuayeu/Plugins-Weave) の ConsiderateCoder プラグイン `skills/dev-rules`・`skills/ops-rules` を参照）
- 実装計画: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)

## Status

**Stage 1-3 完了**（Auth & Client Foundation / Board & Task Fetching / Incremental Sync）。Stage 4 (Rate Limit & Reliability) / Stage 5 (BusinessCurator 連携フォーマット) は未着手 — 詳細は [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)

## Setup

```bash
cp .env.example .env
# .env の JOOTO_API_KEY を編集
```

## Commands

- `/jooto-auth` — API key で `/v1/boards` を叩き、認証成功とアクセス可能なボード数を確認
- `/jooto-list-boards` — アクセス可能な全ボード一覧を取得
- `/jooto-backup` — 指定ボード（または全アクティブボード）の tasks/lists/categories を保存、差分同期（sync_state）に対応

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```
