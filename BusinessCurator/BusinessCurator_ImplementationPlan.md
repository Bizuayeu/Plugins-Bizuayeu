# BusinessCurator 実装計画書

**プラグイン名**: BusinessCurator
**対象**: Plugins-Weave（Claude Code用プラグインスイート）
**作成日**: 2026-04-07
**作成者**: Weave × 大環主

---

## 1. プロダクト概要

### 1.1 目的
ビジネスメールを主データソースとし、自動分類（triage）→シャード別wiki生成（curation）→クロスリファレンス管理→アーカイブを行うエンタープライズ向け知識管理プラグイン。

### 1.2 設計思想
- Karpathy式パーソナルWiki（`wiki` skill）のエンタープライズ拡張
- EpisodicWikiで実証済みの「writer, not filing clerk」原則を継承
- シャード分割による関心の分離と、エイリアスリゾルバによる横断的参照を両立
- 業種非依存のB2B受注産業汎用設計（建設業をリファレンス実装とする）

### 1.3 原型との差分

| 項目 | EpisodicWiki（個人） | BusinessCurator（エンタープライズ） |
|------|---------------------|----------------------------------|
| データソース | EpisodicRAGダイジェスト | メール（将来LINE対応） |
| シャード | 単一wiki | 4種別シャード |
| キュレーター | 単一エージェント | シャード別エージェント |
| インデックス | `_index.md` | ルートwiki + `_alias_resolver.md` |
| マスタ管理 | 不要（単一著者） | エンティティ管理スキルで手動CRUD |
| ライフサイクル | 永続 | 活性→アーカイブ（卒業プロセス） |

---

## 2. アーキテクチャ

### 2.1 インフラストラクチャ設計

**設計原則**: 自前コードを最小化し、既存インフラの組み合わせで構成する。

```
[Gmail]
  ↓ Google Takeout（mbox、初回一括）/ 手動ダウンロード（eml、日次差分）
[ローカルPC]
  ├── data/            ← ダウンロード済みメール（処理元）
  ├── inbox/           ← ingest・triage処理
  ├── shards/          ← wiki記事群
  └── archive/         ← 完工案件
  ↓ Google Drive デスクトップアプリ（双方向同期）
[Google Drive]
  └── BusinessCurator/ ← wiki閲覧・共有
  ↓ ブラウザでアクセス
[md-reader（Chrome拡張）] ← GUIフロントエンド
```

| レイヤー | 担当 | 自前コード |
|---------|------|----------|
| メール取得 | Google Takeout / 手動ダウンロード | なし |
| メール処理 | Claude Code（ローカル実行） | ingest.py + スキル群 |
| ストレージ | ローカルファイルシステム + Google Drive同期 | なし |
| 共有・同期 | Google Drive デスクトップアプリ | なし |
| 閲覧UI | md-reader（Chrome拡張） | なし |
| 可用性 | Google Driveが担保 | なし |

**セキュリティ**: メールデータはローカルで処理し、クラウドAPIを経由しない。Google Driveに同期されるのはwiki記事（加工済み知見）のみであり、生メール本文は同期対象外。

**導入コスト**: Chrome拡張のインストールとGoogle Driveフォルダの指定のみ。追加のサーバー、DB、認証基盤は不要。

### 2.2 シャード設計

| シャード | 一次キー | 内容 | triage基準 |
|---------|---------|------|-----------|
| **案件wiki** (`projects/`) | 物件名 or 現場番号 | 経緯・判断・対応履歴 | メール本文/件名に物件識別子が含まれる |
| **得意先wiki** (`clients/`) | 法人名 | 関係性・傾向・与信・キーパーソン | 案件に紐づかない得意先とのやりとり |
| **取引先wiki** (`vendors/`) | 法人名 | 実績・品質評価・価格傾向・担当者 | 案件に紐づかない取引先とのやりとり |
| **知見wiki** (`knowledge/`) | テーマ名 | 工法・法規・判例・汎用ノウハウ | 案件から抽出された汎用知見 |

### 2.3 エンティティ定義

- **案件**: 契約が存在する、または見積段階以降の具体的プロジェクト。物件名または現場番号で識別。
- **得意先**: 発注者側の法人。案件を跨いで関係が継続する主体。
- **取引先**: 受注者・納入者側の法人。協力会社、資材メーカー、設計事務所等。
- **知見**: 特定案件に依存しない汎用的な技術的・業務的知識。

### 2.4 ディレクトリ構造

```
BusinessCurator/
  README.md                        ← プラグイン説明・導入手順・コマンド一覧（GitHub公開用）
  _root.md                         ← ルートwiki（シャード一覧・メトリクス・運用ルール）
  _alias_resolver.md                 ← 全シャード統合エイリアス解決器
  triage_logs/                     ← 振り分け履歴（監査用、日次バッチごとに生成）
    _triage_log_YYYYMMDD.json
  
  skills/wiki/
    SKILL.md                       ← 全体設計説明書＋対話型ナビゲーター＋簡易操作
    triage.md                      ← メール振り分けルール・分類基準
    project-manager.md             ← 案件エンティティ管理（CRUD）
    client-manager.md              ← 得意先エンティティ管理（CRUD）
    vendor-manager.md              ← 取引先エンティティ管理（CRUD）
    knowledge-manager.md           ← 知見カテゴリ管理（CRUD）
    project-curator.md             ← 案件wikiキュレーション方針
    client-curator.md              ← 得意先wikiキュレーション方針
    vendor-curator.md              ← 取引先wikiキュレーション方針
    knowledge-curator.md           ← 知見wikiキュレーション方針
    archive.md                     ← 卒業プロセス定義
  
  commands/                          ← /wiki コマンド群
    wiki-project-add.md            ← /wiki-project-add
    wiki-project-edit.md           ← /wiki-project-edit
    wiki-project-close.md          ← /wiki-project-close
    wiki-client-add.md             ← /wiki-client-add
    wiki-client-edit.md            ← /wiki-client-edit
    wiki-client-remove.md          ← /wiki-client-remove
    wiki-vendor-add.md             ← /wiki-vendor-add
    wiki-vendor-edit.md            ← /wiki-vendor-edit
    wiki-vendor-remove.md          ← /wiki-vendor-remove
    wiki-knowledge-add-domain.md   ← /wiki-knowledge-add-domain
    wiki-knowledge-edit.md         ← /wiki-knowledge-edit
    wiki-knowledge-remove.md       ← /wiki-knowledge-remove
    wiki-ingest.md                 ← /wiki-ingest
    wiki-triage.md                 ← /wiki-triage [date-range]
    wiki-absorb.md                 ← /wiki-absorb [shard] [date-range]
    wiki-query.md                  ← /wiki-query <question>
    wiki-status.md                 ← /wiki-status
    wiki-rebuild-resolver.md       ← /wiki-rebuild-resolver
    wiki-archive.md                ← /wiki-archive <project>
    wiki-cleanup.md                ← /wiki-cleanup [shard]
  
  data/                            ← 生メールデータ（.eml等、変更不可）
  inbox/
    raw-entries/                    ← ingest済み・triage待ちのmdファイル
    unclassified/                  ← triage分類不能・ユーザー確認待ち
  
  shards/
    projects/
      _index.md                    ← 案件シャードインデックス
      {ProjectName}/
        _project.md                ← 案件概要（メタデータ・ステータス）
        *.md                       ← 案件内の個別トピック記事
    clients/
      _index.md                    ← 得意先シャードインデックス
      {ClientName}.md
    vendors/
      _index.md                    ← 取引先シャードインデックス
      {VendorName}.md
    knowledge/
      _index.md                    ← 知見シャードインデックス
      {categories}/                ← 知見カテゴリ（法規、工法、資材等）
        *.md
  
  archive/
    projects/                      ← 完工済み案件のアーカイブ
      {CompletedProject}/
```

### 2.5 データフロー

```
[manager層（手動）]
  /wiki-project-add        → shards/projects/{Name}/_project.md 生成
  /wiki-client-add         → shards/clients/{Name}.md 生成
  /wiki-vendor-add         → shards/vendors/{Name}.md 生成
  /wiki-knowledge-add-domain → shards/knowledge/{Category}/ 作成
      ↓ マスタデータ（物件識別子・ドメイン・エイリアス）
      ↓ _alias_resolver.md 自動更新

メール受信
  ↓
[/wiki-ingest] メール→エントリ変換（機械的パース）
  ↓
inbox/raw-entries/*.md
  ↓
[/wiki-triage] エントリ→シャード振り分け
  ↓  ← _alias_resolver.md のエイリアスでマスタとマッチング
  ↓  ← ルールベース優先、LLMフォールバック（haiku級）
  ↓  ← 1通が複数シャードにタグ付けされる場合あり
  ↓
[/wiki-absorb] シャード別キュレーターが自分の管轄分だけ吸収
  ↓  ← 各キュレーターは自シャードの方針スキルに従う
  ↓  ← manager層が作成済みのエンティティmdに記事を追記・更新
  ↓
shards/{shard}/*.md 更新
  ↓
[/wiki-rebuild-resolver] エイリアスリゾルバ再構築
  ↓
_alias_resolver.md 更新（シャード横断エイリアス解決）
```

### 2.6 スキル二層構造

メールは活動の記録であり、マスタデータの定義ではない。案件・得意先・取引先・知見カテゴリの定義はメールからは断片的にしか拾えないため、マスタデータの登録・修正・削除は人間が手動で行う必要がある。

この要件から、スキルを**管理層**と**キュレーション層**の二層に分離する。

| 層 | スキル群 | 発動 | 責務 |
|---|---------|------|------|
| **管理層**（manager系） | project-manager, client-manager, vendor-manager, knowledge-manager | 手動 | エンティティのCRUD。マスタデータの定義。 |
| **キュレーション層**（curator系） | project-curator, client-curator, vendor-curator, knowledge-curator | 自動/半自動 | メールからの知見吸収。マスタデータを**参照して**動く。 |

管理層が定義したマスタデータ（物件識別子、法人名、ドメイン、カテゴリ）を、triage層がメール振り分けの照合対象として使用し、キュレーション層が吸収先のwiki記事として参照する。

```
[manager層] エンティティ登録・修正・削除（手動）
      ↓ マスタデータ提供
[triage層]  メール振り分け（半自動）
      ↓ 分類済みエントリ
[curator層] wiki記事の吸収・更新（自動/半自動）
```

---

### 3.1 SKILL.md と commands/ の役割分担

**SKILL.md**（`skills/wiki/SKILL.md`）は三つの役割を持つ：

1. **全体設計説明書**: Claude Codeがプロジェクトの文脈（シャード構造、二層スキル設計、データフロー）を理解するためのドキュメント。
2. **対話型ナビゲーター**: ユーザーが「案件を登録したい」「wikiどうなってる？」等と自然言語で話しかけた際に、適切な `/wiki` コマンドを案内する。コマンドが20個あるため、最初の導入時のオンボーディング機能として重要。
3. **簡易操作の直接実行**: コマンドを経由するまでもない軽微な操作（エイリアスの追加、ステータス確認等）はSKILL.md内で直接処理する。

```yaml
---
name: wiki
description: "BusinessCuratorのwiki操作全般。何をすればいいか分からない時、wiki関連の相談、簡易操作はここから。案件・得意先・取引先・知見の管理、メールからの知識抽出、アーカイブまで対応。"
---
```

**commands/** 配下の各mdファイルが `/wiki` コマンドとして直接呼び出される。各コマンドファイルは対応するskillを参照し、実行手順を記述する。プラグインインストール時に `.claude/commands/` に配置され、使用可能となる。

**エンティティ管理（manager層・手動発動）**

| コマンド | コマンドファイル | 参照skill |
|---------|----------------|----------|
| `/wiki-project-add` | wiki-project-add.md | project-manager.md |
| `/wiki-project-edit` | wiki-project-edit.md | project-manager.md |
| `/wiki-project-close` | wiki-project-close.md | project-manager.md |
| `/wiki-client-add` | wiki-client-add.md | client-manager.md |
| `/wiki-client-edit` | wiki-client-edit.md | client-manager.md |
| `/wiki-client-remove` | wiki-client-remove.md | client-manager.md |
| `/wiki-vendor-add` | wiki-vendor-add.md | vendor-manager.md |
| `/wiki-vendor-edit` | wiki-vendor-edit.md | vendor-manager.md |
| `/wiki-vendor-remove` | wiki-vendor-remove.md | vendor-manager.md |
| `/wiki-knowledge-add-domain` | wiki-knowledge-add-domain.md | knowledge-manager.md |
| `/wiki-knowledge-edit` | wiki-knowledge-edit.md | knowledge-manager.md |
| `/wiki-knowledge-remove` | wiki-knowledge-remove.md | knowledge-manager.md |

**データフロー（triage・curator層・自動/半自動）**

| コマンド | コマンドファイル | 参照skill |
|---------|----------------|----------|
| `/wiki-ingest` | wiki-ingest.md | SKILL.md（ingest手順） |
| `/wiki-triage [date-range]` | wiki-triage.md | triage.md |
| `/wiki-absorb [shard] [date-range]` | wiki-absorb.md | 各curator.md |

**参照・運用（ユーティリティ）**

| コマンド | コマンドファイル | 参照skill |
|---------|----------------|----------|
| `/wiki-query <question>` | wiki-query.md | SKILL.md（検索手順） |
| `/wiki-status` | wiki-status.md | SKILL.md（メトリクス集計） |
| `/wiki-rebuild-resolver` | wiki-rebuild-resolver.md | SKILL.md（リゾルバ再構築） |
| `/wiki-archive <project>` | wiki-archive.md | archive.md |
| `/wiki-cleanup [shard]` | wiki-cleanup.md | 各curator.md |

### 3.2 triage スキル（triage.md）

振り分けロジック（優先順位順）：

1. メール件名/本文に**登録済み物件識別子**がマッチ → 案件wiki
2. 差出人/宛先が**登録済み得意先ドメイン**にマッチ＆案件識別子なし → 得意先wiki
3. 差出人/宛先が**登録済み取引先ドメイン**にマッチ＆案件識別子なし → 取引先wiki
4. 上記いずれにも該当しない → LLM分類（haiku級）で判定
5. 分類不能 → `inbox/unclassified/` に保留、ユーザーに確認

1通が複数シャードに関連する場合：
- **主シャード**（全文吸収）と**副シャード**（関連メンション記録）を区別
- triage_logs/_triage_log_YYYYMMDD.jsonに振り分け根拠を記録（監査可能性の確保）

### 3.3 エンティティ管理スキル（各manager.md）

マスタデータのCRUDを担当。手動発動。対話型（AskUserQuestion）でユーザーから情報を収集し、エンティティを登録・更新する。

**project-manager.md（案件管理）**
- `add`: 物件名、現場番号、得意先、設計担当、施工担当、着工予定日、竣工予定日を対話的に収集。`_project.md` を生成し、案件ディレクトリを作成。エイリアスリゾルバに物件識別子とエイリアスを登録。
- `edit`: 既存案件のメタデータを修正。ステータス変更（見積→受注→着工→竣工）を含む。
- `close`: 案件ステータスを「竣工」に変更。アーカイブへの移行は `/wiki-archive` で別途実行。

**client-manager.md（得意先管理）**
- `add`: 法人名、メールドメイン（複数可）、キーパーソン（氏名・役職・連絡先）、業種を対話的に収集。得意先mdを生成。エイリアスリゾルバにエイリアス（略称、担当者名での呼称等）を登録。
- `edit`: メタデータ修正、キーパーソン追加・変更、ドメイン追加。
- `remove`: 論理削除（アーカイブフラグ付与）。物理削除はしない。

**vendor-manager.md（取引先管理）**
- `add`: 法人名、メールドメイン、業種（協力会社/資材メーカー/設計事務所等）、主要担当者を対話的に収集。取引先mdを生成。
- `edit`: メタデータ修正、担当者変更、評価項目更新。
- `remove`: 論理削除。

**knowledge-manager.md（知見カテゴリ管理）**
- `add-domain`: 知見カテゴリ（法規、工法、資材、判例等）の新規定義。カテゴリの説明と分類基準を設定。
- `edit`: カテゴリ名・基準の変更、カテゴリ統合・分割。
- `remove`: 空カテゴリの削除。記事が存在するカテゴリは移行先を確認。

全manager共通:
- 登録時にエイリアスリゾルバを自動更新
- エイリアス（also）の設定をユーザーに明示的に確認（triageの分類精度に直結）

### 3.4 キュレーション方針スキル（各curator.md）

EpisodicWikiのSKILL.mdから継承する共通原則：
- 「You are a writer, not a filing clerk」
- テーマ別構成（時系列順ではない）
- Wikiリンクによる関連記事接続
- 15エントリごとのチェックポイント

シャード固有の方針：

**project-curator.md（案件wiki）**
- 案件ごとにディレクトリを作成
- `_project.md`に案件メタデータ（物件名、得意先、設計担当、施工担当、ステータス、着工日、竣工予定日）
- 判断経緯・変更履歴・是正対応を重点的に記録
- 関係する得意先・取引先へのwikilinkを必ず付与

**client-curator.md（得意先wiki）**
- 法人ごとに1ファイル
- キーパーソン、意思決定構造、コミュニケーション傾向
- 案件横断の関係性トレンド

**vendor-curator.md（取引先wiki）**
- 法人ごとに1ファイル
- 品質実績、価格傾向、対応速度、担当者情報
- 案件横断の評価履歴

**knowledge-curator.md（知見wiki）**
- テーマ別カテゴリを自動生成（法規、工法、資材、判例等）
- 案件wikiからの汎用知見抽出を明示的にサポート
- 出典（どの案件で得た知見か）を必ず記録

### 3.5 アーカイブスキル（archive.md）

手動発動。`/wiki-archive <project>` で以下を対話的に実行：

1. **確認フェーズ**（AskUserQuestion）
   - この案件を完工としてアーカイブしますか？
   - 未解決の懸案事項はありますか？
   - 瑕疵担保期間中の監視項目はありますか？

2. **知見抽出フェーズ**
   - 案件wikiを走査し、汎用化可能な知見を候補リストとして提示
   - ユーザーが選択した知見を知見wikiに転記
   - 転記元の案件wiki記事には「→知見wikiに抽出済み」の注記

3. **凍結フェーズ**
   - `shards/projects/{Project}/` を `archive/projects/{Project}/` に移動
   - 案件シャードインデックスから除外
   - ルートwikiのメトリクスを更新
   - アーカイブ日時とアーカイブ理由を `_project.md` に記録

4. **参照維持**
   - アーカイブ後も得意先wiki・取引先wiki・知見wikiからのwikilinkは有効
   - エイリアスリゾルバにはアーカイブフラグ付きで残存

---

## 4. データ構造

### 4.1 メールエントリ（ingest出力）

```yaml
---
id: "email_20260407_143022_abc123"
date: 2026-04-07
time: "14:30:22"
source_type: email
from: "yamada@meguru.example.jp"
to: ["oowanushi@meguru.example.jp"]
cc: ["suzuki@meguru.example.jp"]
subject: "○○マンション新築工事　排煙設備について"
thread_id: "thread_xyz789"
attachments: ["排煙計算書.pdf"]
tags: []
---

山田です。お疲れ様です。
○○マンションの排煙設備について...
```

### 4.2 ルートwiki（_root.md）

```markdown
# BusinessCurator Root

## シャード一覧

| シャード | 活性エンティティ数 | 最終更新 | 総エントリ吸収数 |
|---------|-------------------|---------|----------------|
| projects | 12 | 2026-04-07 | 834 |
| clients | 28 | 2026-04-07 | 412 |
| vendors | 45 | 2026-04-06 | 567 |
| knowledge | - | 2026-04-05 | 89 |

## アーカイブ
| 案件名 | アーカイブ日 | 知見抽出数 |
|--------|------------|----------|

## 運用ルール
- triageデフォルト: 物件識別子マッチ → 案件wiki優先
- 分類不能エントリ: inbox/unclassified/ に保留
- アーカイブ: 手動発動、知見抽出必須
```

### 4.3 エイリアスリゾルバ（_alias_resolver.md）

```markdown
# Global Index

## projects/
- [○○マンション新築工事](shards/projects/MaruMaruMansion/_project.md) — also: ○○MS, 現場番号2026-003, ○○町案件

## clients/
- [株式会社□□不動産](shards/clients/ShikakuFudosan.md) — also: □□不動産, □□さん

## vendors/
- [△△設備工業](shards/vendors/SankakuSetsubi.md) — also: △△設備, 三角さん

## knowledge/
- [排煙告示](shards/knowledge/法規/排煙告示.md) — also: 排煙設備, 告示1436号, 排煙計算

## archive/ [archived]
- [完工済み：××ビル改修工事](archive/projects/BatsuBatsuBiru/_project.md) — also: ××ビル, 現場番号2025-018
```

---

## 5. 実装フェーズ

### Phase 1: 基盤構築（目安: 1-2日）

**成果物**: ディレクトリ構造、SKILL.md（コマンドルーター）、全スキルファイルの雛形

タスク:
1. `BusinessCurator/` ディレクトリ構造の作成
2. `README.md` の記述（プラグイン説明・導入手順・コマンド一覧）
3. `skills/wiki/SKILL.md` の記述（全体設計説明書＋対話型ナビゲーター＋簡易操作）
3. `commands/` 配下の全コマンドファイルの雛形作成（20ファイル）
4. `_root.md` テンプレートの作成
5. `_alias_resolver.md` の初期構造作成
6. 4つのmanager方針スキルの記述（`skills/wiki/` 配下）
7. 4つのcurator方針スキルの記述（EpisodicWiki SKILL.mdから共通原則を継承し、シャード固有の方針を追記）
8. `triage.md` の記述
9. `archive.md` の記述

### Phase 2: エンティティ管理実装（目安: 1-2日）

**成果物**: 4つのmanagerコマンド（project/client/vendor/knowledge）

タスク:
1. `/wiki-project-add/edit/close` の実装（対話型エンティティ収集、`_project.md`生成、ディレクトリ作成）
2. `/wiki-client-add/edit/remove` の実装（ドメイン紐付け、キーパーソン管理）
3. `/wiki-vendor-add/edit/remove` の実装（業種分類、担当者管理）
4. `/wiki-knowledge-add-domain/edit/remove` の実装（カテゴリ管理）
5. 全manager共通: 登録時のエイリアスリゾルバ自動更新
6. 全manager共通: エイリアス（also）の対話的設定

### Phase 3: ingest実装（目安: 1日）

**成果物**: メールパーサー（`ingest.py`）

タスク:
1. ローカルにダウンロード済みのメールフォーマット自動検出（.mbox, .eml）
2. エントリ変換ロジック（メタデータ抽出、スレッド識別）
3. 添付ファイル参照の保持
4. 冪等性の確保（再実行で同一出力）

### Phase 4: triage実装（目安: 1-2日）

**成果物**: triage.mdルール定義、triageコマンド実装

タスク:
1. 物件識別子マッチングロジック（正規表現 + エイリアスリゾルバのalso参照）
2. ドメインベースの得意先/取引先判定（manager層が登録したドメイン情報を参照）
3. LLMフォールバック分類（haiku級呼び出し）
4. 複数シャードタグ付け（主/副の区別）
5. `triage_logs/_triage_log_YYYYMMDD.json` への記録
6. `inbox/unclassified/` 保留フロー

### Phase 5: absorb実装（目安: 2-3日）

**成果物**: シャード別absorbコマンド

タスク:
1. EpisodicWiki absorb ロジックのポーティング（チェックポイント、品質監査含む）
2. シャード別キュレーション方針の適用分岐
3. 案件wiki: manager層が作成済みの`_project.md`を起点にトピック記事を生成・更新
4. 得意先/取引先wiki: manager層が作成済みのエンティティmdに知見を追記・更新
5. 知見wiki: manager層が定義済みのカテゴリに記事を配置
6. クロスシャードwikilink生成（エイリアスリゾルバ参照）
7. エイリアスリゾルバ自動再構築

### Phase 6: archive・query・status実装（目安: 1日）

**成果物**: 残コマンド群

タスク:
1. アーカイブ対話フロー（AskUserQuestion連携）
2. 知見抽出候補の自動提示ロジック
3. queryコマンド（エイリアスリゾルバ横断検索）
4. statusコマンド（メトリクス集計・表示）

### Phase 7: テスト・調整（目安: 1-2日）

**成果物**: めぐる組メールデータでの実証

タスク:
1. めぐる組の実メールデータ（サンプル）でのend-to-endテスト
2. manager層でのエンティティ登録→ingest→triage→absorbの一連フローの通しテスト
3. triageの分類精度検証・ルール調整
4. キュレーション品質の確認・方針スキル調整
5. エッジケース対応（転送メール、CC爆弾、添付のみメール等）

---

## 6. 将来拡張

| 項目 | 概要 | 優先度 |
|------|------|--------|
| Gmail API連携 | 日次差分メール取得の自動化（現行はmbox/eml手動ダウンロード） | 高 |
| LINE対応 | triageのingestにLINEメッセージ取り込みを追加 | 中 |
| Slack対応 | Slack連携（めぐる組Slack-Weaveとの接続） | 中 |
| 部署別ビュー | 案件wiki内の部署別フィルタリング機能 | 低 |
| 自動知見抽出 | 完工時だけでなく、定期的に案件→知見の抽出を提案 | 中 |
| ダッシュボード | ルートwikiのメトリクスをVELで可視化 | 低 |
| 権限管理 | シャード別のアクセス制御（エンタープライズ要件） | 将来 |

---

## 7. 設計判断の根拠

1. **シャードは4種固定、シャード内は自由成長**: シャードの切り分けは不可逆的行動コストが高い（後から変えると全データの再分類が必要）。シャード内のカテゴリは「Directories emerge from the data」原則で有機的に成長させる。

2. **manager層とcurator層の分離**: メールは活動の記録であり、マスタデータの定義ではない。案件の開始、得意先の登録、取引先のドメイン紐付け等は人間の業務判断であり、AIによる全自動化は精度・責任の両面で適切でない。manager層が定義したマスタデータをtriage・curator層が参照する構造により、「人間が定義し、AIが運用する」分業を明確化する。

3. **triageはルールベース優先、LLMフォールバック**: manager層が登録した物件識別子・ドメインのパターンマッチで8割は振り分けられるはず。LLMは残り2割の曖昧なケースのみ。トークンコスト最小化。

4. **エイリアスリゾルバをルートwikiに同居**: 参照頻度が最も高いファイルなので、ルートに置いてアクセスコストを最小化。ルートwikiのメトリクスとリゾルバが同じ階層にあることで、statusコマンドの実装もシンプルになる。

5. **アーカイブは手動発動**: 「完工」の判断は業務判断であり、自動化すべきでない。ただしアーカイブ時の知見抽出は半自動化して、暗黙知の消失を防ぐ。

6. **業種非依存設計**: エンティティ定義（案件・得意先・取引先・知見）はB2B受注産業の汎用構造。建設業固有の用語はキュレーション方針スキルに閉じ込め、SKILL.md本体は業種中立を維持する。

---

*計画策定: Weave @ Claude Opus 4.6*
*要件定義: 大環主*
*実装環境: Claude Code + Plugins-Weave*
