# Changelog

JootoGrabber の変更履歴。

## [0.1.0] - 2026-04-14

### Added

- Jooto API クライアント基盤（Stage 1）— API Key 認証（`X-Jooto-Api-Key` ヘッダ）、Base URL `https://api.jooto.com`。設定は `.env`（雛形は `.env.example`）。
- ボード／タスク取得（Stage 2）— tasks / lists / categories を BusinessCurator が吸収可能な JSON として出力する。
- 差分同期（Stage 3）— `sync_state` を用いた incremental sync。
- コマンド 3 種 — `/jooto-auth`（`/v1/boards` で疎通とアクセス可能ボード数を確認）／`/jooto-list-boards`（全ボード一覧）／`/jooto-backup`（指定ボードまたは全アクティブボードの保存）。
- Clean Architecture + TDD 構成（domain / application / infrastructure / interfaces）とテストスイート。

### Notes

- Stage 4（Rate Limit & Reliability）／Stage 5（BusinessCurator 連携フォーマット）は未着手。詳細は [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)。
