# BusinessCurator

エンタープライズ向けビジネスメール知識管理プラグイン (Claude Code)。
Karpathy 式パーソナル wiki (`wiki` skill) の **エンタープライズ拡張**として、
ビジネスメールを 4 シャード wiki に編み込みます。

> **writer, not filing clerk** — 事実をどこに置くかではなく、それが何を意味し、既存の理解にどう繋がるかを問い続ける。

---

## 主要特徴

- **4 シャード固定**: projects / clients / vendors / knowledge
- **二層構造**: マスタは人間が定義 (manager) し、AI が運用 (curator) する
- **triage はルールベース優先**: 80% をルールで決着、20% を LLM (`claude -p` subprocess) で
- **archive は手動発動**: 完工判断は業務判断、知見抽出は半自動化
- **md / Python 二層分離**: 機械的処理は Python、判断と対話は md
- **Clean Architecture × TDD**: domain → application → infrastructure → interfaces

---

## クイックスタート

```bash
# 1. 状態確認
/wiki-status

# 2. マスタ登録
/wiki-project-add ○○マンション
/wiki-client-add 株式会社□□

# 3. メール取り込み → 振り分け → 吸収
/wiki-ingest data/sample.mbox
/wiki-triage
/wiki-absorb projects

# 4. 完工アーカイブ
/wiki-archive ○○マンション
```

詳細は `[skills/wiki/SKILL.md](skills/wiki/SKILL.md)` を参照。

---

## 全 23 コマンド

### Manager 層 (マスタ CRUD、12 commands)

| カテゴリ | コマンド |
|---|---|
| Project | `/wiki-project-add` `/wiki-project-edit` `/wiki-project-close` |
| Client | `/wiki-client-add` `/wiki-client-edit` `/wiki-client-remove` |
| Vendor | `/wiki-vendor-add` `/wiki-vendor-edit` `/wiki-vendor-remove` |
| Knowledge | `/wiki-knowledge-add-domain` `/wiki-knowledge-edit` `/wiki-knowledge-remove` |

### Operation 層 (運用、5 commands)

| コマンド | 用途 |
|---|---|
| `/wiki-ingest` | data/ → inbox/raw-entries/ |
| `/wiki-triage` | raw-entries/ をシャードに振り分け |
| `/wiki-absorb` | shards/ にエントリを吸収 |
| `/wiki-jooto-absorb` | JootoGrabber export (data/jooto/) を wiki に吸収 |
| `/wiki-archive` | 完工案件を archive/ へ |

### Auxiliary 層 (補助、6 commands)

| コマンド | 用途 |
|---|---|
| `/wiki-query` | wiki 横断質問応答 |
| `/wiki-status` | シャード横断メトリクス |
| `/wiki-rebuild-resolver` | エイリアスリゾルバ再構築 |
| `/wiki-index-rebuild` | `_index.md` ツリー再生成 |
| `/wiki-verify-links` | wikilink 整合性検証 (broken / stale link 検出) |
| `/wiki-cleanup` | 既存記事の品質改善 |

---

## ディレクトリ構造

```
BusinessCurator/
  README.md
  pyproject.toml
  BusinessCurator_ImplementationPlan.md       ← 業務観点
  BusinessCurator_TDDImplementationPlan.md    ← 実装観点
  _root.md                                    ← ルート wiki
  _alias_resolver.md                            ← 全シャード統合エイリアス解決器

  skills/wiki/                                ← 12 skill md
  commands/                                   ← 23 command md

  scripts/                                    ← Clean Architecture 実装
    domain/                                   ← 純粋型・例外・Protocol・IndexEntry
    application/                              ← UseCase (resolver/archive/quality/indexing/status)
    infrastructure/                           ← 実 I/O アダプタ・migrations
    interfaces/                               ← CLI (Composition Root)
    test/                                     ← 645 tests

  ── 以下は wiki インスタンス側（実行時に plugin_root 起点で生成、配布物ではない）──
  data/                                       ← 生メール (.eml/.mbox、変更不可)
  inbox/
    raw-entries/                              ← ingest 出力
    unclassified/                             ← triage 保留
  shards/
    projects/{Name}/_project.md
    clients/{Name}.md
    vendors/{Name}.md
    knowledge/{Category}/*.md
  archive/projects/{CompletedName}/
  triage_logs/_triage_log_YYYYMMDD.json
```

> wiki インスタンス側の実体は運用環境にのみ存在する。本リポジトリ（DEV チェックアウト）に置かれるのは配布物層（`skills/` / `commands/` / `scripts/` / `docs/`）だけである。

---

## アーキテクチャ

### Clean Architecture 4 層

```
interfaces ──→ application ──→ domain
     │              │              ↑
     │              └──Protocol────┘
     │                             ↑
     └──→ infrastructure ──────────┘
```

- **domain**: 何にも依存しない純粋型 (TypedDict / Protocol / 例外 / 純関数)
- **application**: domain の Protocol にのみ依存。UseCase の実装
- **infrastructure**: domain/application 双方を参照。Protocol を実装
- **interfaces**: 全層に依存可能。Composition Root として infrastructure 実装を application に注入

### md / Python 二層分離

| 処理 | 配置 | 理由 |
|---|---|---|
| ingest / triage / status / archive 操作 | Python CLI | 機械的・冪等・テスト可能 |
| Manager の CRUD 対話 | md (manager skill) | AskUserQuestion + 判断 |
| Curator のキュレーション | md (curator skill) | LLM の "writer" 判断が本質 |
| Triage LLM フォールバック | md → `claude -p` subprocess | API 直叩き禁止原則 |

---

## 開発

### 必要環境

- Python 3.10+
- Claude Code (CLI、`claude` コマンド)
- pip install されるテスト依存: `pytest~=8.0`, `pytest-cov~=6.0`, `mypy~=2.3.0`, `ruff~=0.16.0`, `hypothesis~=6.122`

### テスト実行

```bash
cd plugins-bizuayeu/BusinessCurator

# 全テスト + カバレッジ
python -m pytest scripts/test/ --cov=scripts --cov-fail-under=80

# レイヤ別
python -m pytest scripts/test/domain_tests/ -v
python -m pytest scripts/test/application_tests/ -v
python -m pytest scripts/test/infrastructure_tests/ -v
python -m pytest scripts/test/cli_integration_tests/ -v
python -m pytest scripts/test/integration_tests/ -v       # E2E
python -m pytest scripts/test/skill_structure_tests/ -v   # md 構造

# 統計
python -m pytest scripts/test/ -q --no-cov
# → 645 passed
```

### 静的解析

```bash
python -m mypy scripts/ --strict
# → Success: no issues found in 100+ source files

python -m ruff check scripts/
# → All checks passed!
```

### CLI 出力スキーマ

全 CLI の JSON 出力スキーマは `[scripts/interfaces/CLI_OUTPUT_SCHEMAS.md](scripts/interfaces/CLI_OUTPUT_SCHEMAS.md)` を参照。

### 手動 E2E シナリオ

`[docs/manual_e2e_scenarios.md](docs/manual_e2e_scenarios.md)` に4つのシナリオを記載：
1. 案件登録から absorb まで通し
2. 完工アーカイブの対話フロー
3. triage ルール改善ループ
4. LLM フォールバック動作確認

---

## 品質指標

| 項目 | 値 |
|---|---|
| **テスト数** | **645 passed** |
| **カバレッジ** | fail_under=80 |
| **mypy strict** | 111 source files checked |
| **ruff** | 有効 |
| **md ファイル数** | **35** (12 skill + 23 command) |
| **TDD サイクル** | Red → Green → Refactor を全機能で遵守 |

---

## 設計判断の根拠

業務観点の根拠は `BusinessCurator_ImplementationPlan.md`、実装観点の根拠は `BusinessCurator_TDDImplementationPlan.md` を参照。

### 主要原則

1. **シャードは4種固定、シャード内は自由成長**: シャード境界変更は不可逆コストが高い
2. **manager 層と curator 層の分離**: マスタは人間が定義、AI が運用
3. **triage はルールベース優先**: トークンコスト最小化
4. **エイリアスリゾルバをルートに同居**: アクセスコスト最小化
5. **archive は手動発動**: 完工判断は業務判断
6. **業種非依存設計**: B2B 受注産業の汎用構造

---

## Changelog

### v1.1.0 (2026-07-04)

- **`/wiki-jooto-absorb`**: JootoGrabber が export したボード/タスク JSON を wiki に吸収するコマンド + `jooto-absorb` スキル（実装は 2026-04-14、本リリースで版数・ドキュメントに記録化）
- ドキュメント整合: コマンド数 23 / skill md 12 へ統計更新、SKILL.md 運用層テーブルに jooto-absorb を掲載

### v1.0.0 (2026-04-12)

- **archive_status 3 状態統一**: `archived: bool` → `archive_status: Literal["active","completed","removed"]`。AliasRecord + ShardEntity 同時移行、後方互換性なし
- **complete_archive()**: 完工アーカイブの atomic メソッド。旧 `edit + remove` 2 段階呼びを廃止
- **Repository 3 セクション化**: `## archive/<kind>/ [completed]` / `[removed]` で kind 別に archive セクション分離
- **Migration script**: `infrastructure/migrations/migrate_to_archive_status.py` (旧 `## archive/ [archived]` → 新フォーマット一発変換)
- **wikilink_verifier**: `application/quality/wikilink_verifier.py` + `interfaces/quality_cli.py` で broken/stale link を production 検出
- **`/wiki-index-rebuild`**: `_index.md` ツリー再生成コマンド
- **`/wiki-verify-links`**: wikilink 整合性検証コマンド
- **thread_id regression tests**: production の thread_id 非汚染を 4 件のテストで永続保証
- テスト数: 589 → **645** (+56)

### v0.1.0 (2026-04-07)

- 初回リリース: Clean Architecture × TDD、4 シャード wiki、20 コマンド

---

## ライセンス

MIT

---

## クレジット

- 計画策定: Weave @ Claude Opus 4.6 (1M context)
- 要件確認: 大環主
- 実装環境: Claude Code + Plugins-Weave

参照プラグイン:
- `[wiki](skills/wiki/SKILL.md)` (Karpathy 式パーソナル wiki) — 原型
- `[EpisodicRAG](../../plugins-weave/EpisodicRAG/)` — Clean Architecture × TDD パターン提供
