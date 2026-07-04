# JootoGrabber Implementation Plan

Jooto API からボード/タスクを取得し、BusinessCurator が吸収可能な形式で出力する Claude Code プラグイン。

- 参考: [Jooto API Reference](https://www.jooto.com/api/reference/authentication/)
- 設計方針: Clean Architecture + TDD（開発規範は [Plugins-Weave](https://github.com/Bizuayeu/Plugins-Weave) の ConsiderateCoder プラグイン `skills/dev-rules`・`skills/ops-rules` を参照）
- 既存姉妹プラグイン: [GmailGrabber](../GmailGrabber/) を構造のテンプレートとする

---

## 規模前提

- 対象ボード数: **約30**
- 想定タスク総数: 数千規模（差分同期で運用）
- 認証: API Key（1ユーザー = 1 key、env var 管理）

---

## 成果物

```
JootoGrabber/
├── .claude-plugin/plugin.json
├── README.md
├── pyproject.toml                  ← GmailGrabber 準拠
├── commands/
│   ├── jooto-auth.md               ← API key 登録・検証
│   ├── jooto-list-boards.md        ← ボード一覧取得
│   ├── jooto-backup.md             ← 単一ボード全タスク取得
│   └── jooto-sync.md               ← 差分同期（updated_at ベース）
├── skills/                         ← 必要に応じて
├── scripts/
│   ├── domain/
│   │   ├── board.py                ← Board, List, Task 値オブジェクト
│   │   └── sync_state.py           ← 差分判定ロジック
│   ├── application/
│   │   ├── fetch_boards.py
│   │   ├── fetch_tasks.py
│   │   └── sync_usecase.py
│   ├── infrastructure/
│   │   ├── jooto_client.py         ← HTTP クライアント（認証・retry・rate limit）
│   │   └── storage.py              ← data/jooto/ への JSON 書き出し
│   ├── interfaces/
│   │   └── cli.py
│   └── test/
└── docs/
    └── API_NOTES.md                ← Jooto API の癖・ページング・レート制限メモ
```

---

## Stage 1: Auth & Client Foundation

**Goal**: Jooto API への認証と最小限の GET が通る。
**Success Criteria**:
- `JOOTO_API_KEY` を env/`.env` から読み込む
- `/jooto-auth` が `GET /users/me`（または同等）で 200 を返す
- HTTP 層は interface 経由で差し替え可能
**Tests**:
- unit: API key 未設定時のエラー、ヘッダ組み立て
- unit: 401/403/429 の例外マッピング
- integration: モックサーバ or recorded response で /users/me パース
**Status**: Complete

## Stage 2: Board & Task Fetching

**Goal**: ボード一覧とボード配下の全タスクを取得・保存。
**Success Criteria**:
- `/jooto-list-boards` が board 一覧を表示
- `/jooto-backup --board <id>` が `data/jooto/{board_slug}/tasks.json` に保存
- ページングを透過的に処理
**Tests**:
- unit: ページング終了条件、空レスポンス
- property: 任意のタスク数 N に対し `len(fetched) == N`
- integration: 固定 fixture でのフルフェッチ
**Status**: Complete

## Stage 3: Incremental Sync

**Goal**: 差分同期で30ボード運用を現実的なコストで回す。
**Success Criteria**:
- `data/jooto/{board_slug}/_sync_state.json` に last_synced_at を保存
- 2回目以降は updated_at > last_synced_at のみ取得
- 削除タスクの検出（tombstone か全件再取得 fallback）
**Tests**:
- unit: sync_state の読み書き・破損時の再構築
- integration: 2段階フェッチで差分のみ更新されることを確認
**Status**: Complete

## Stage 4: Rate Limit & Reliability

**Goal**: 30ボードの一括同期でもレート制限に耐える。
**Success Criteria**:
- 429 受信時の exponential backoff（最大 N 回リトライ）
- `--dry-run` でリクエスト数を事前見積
- 部分失敗時の再開可能性（board 単位の冪等性）
**Tests**:
- unit: backoff スケジュールの正しさ
- integration: 429 を返すモックでリトライと最終成功
**Status**: Not Started

## Stage 5: BusinessCurator 連携フォーマット

**Goal**: BusinessCurator の `/wiki-jooto-absorb`（別途追加）が消費できる形式で出力。
**Success Criteria**:
- タスク 1 件 = `{task_id, board, list, title, assignees, due, status, updated_at, url, description}` の JSON
- プロジェクト Slug 解決ヒントフィールド（board名・ラベル等）を含める
- BusinessCurator 側の alias_resolver と突き合わせ可能
**Tests**:
- unit: シリアライズの安定性（keys ソート、改行正規化）
- integration: 実データスキーマの schema-validation
**Status**: Not Started

---

## Open Questions

1. **Jooto API のレート制限上限** — 公式 docs で要確認（Stage 4 の設計に影響）
2. **タスクコメント/チェックリスト取得** — 別エンドポイント想定、MVP では含めるか？
3. **Slug 解決戦略** — Jooto board 名 ↔ MeguruWiki project slug のマッピングを
   (a) board 名正規化で自動解決 / (b) 明示マッピングファイル / (c) BusinessCurator 側で resolver に委譲
4. **secret 管理** — `.env` / macOS keychain / Claude Code の settings どれを基準にするか

---

## Non-Goals (このフェーズでは扱わない)

- Jooto への書き戻し（read-only）
- Webhook / リアルタイム同期
- 他プロジェクト管理ツール（Asana, Trello 等）への一般化
