# Changelog

JootoGrabber の変更履歴。

## [0.2.0] - 2026-08-25 — 静的チェックをワークスペース基準へ揃える

コードの挙動は変えていない。ワークスペースに 2 つ併存していた ruff/mypy の流儀を
和集合（広い lint ＋ strict な mypy）へ寄せる作業の一環。

### Changed

- ruff の `select` を `E,W,F,I` から `E4,E7,E9,F,I,UP,N,B,SIM,PTH` へ拡張。狭い網では
  CI が green のまま旧記法・危険記法（`B904` の例外連鎖切断、`SIM115` のリソース未解放、
  `PTH` の `os.path` 残存）が溜まる。**型検査ではこの類は出ない**
- `E501` は新集合に含まれない（`E4`/`E7`/`E9` のみ）ため `ignore` から落とし、行長の判断を
  formatter へ一本化
- formatter をワークスペース既定へ（`line-length = 100` と `quote-style = "preserve"` を撤去
  ＝ 88 桁・クオート正規化）。9 ファイルが再整形された

### Fixed

- `UP035` 6 件（`typing.Mapping` / `Iterator` / `Sequence` → `collections.abc`）
- `UP028` 1 件（`paginator`: `for item in ...: yield item` → `yield from`）

### 検証

ruff 7→0 ／ mypy Success ／ pytest 39 passed（前後一致）

## [0.1.0] - 2026-04-14

### Added

- Jooto API クライアント基盤（Stage 1）— API Key 認証（`X-Jooto-Api-Key` ヘッダ）、Base URL `https://api.jooto.com`。設定は `.env`（雛形は `.env.example`）。
- ボード／タスク取得（Stage 2）— tasks / lists / categories を BusinessCurator が吸収可能な JSON として出力する。
- 差分同期（Stage 3）— `sync_state` を用いた incremental sync。
- コマンド 3 種 — `/jooto-auth`（`/v1/boards` で疎通とアクセス可能ボード数を確認）／`/jooto-list-boards`（全ボード一覧）／`/jooto-backup`（指定ボードまたは全アクティブボードの保存）。
- Clean Architecture + TDD 構成（domain / application / infrastructure / interfaces）とテストスイート。

### Notes

- Stage 4（Rate Limit & Reliability）／Stage 5（BusinessCurator 連携フォーマット）は未着手。詳細は [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)。
