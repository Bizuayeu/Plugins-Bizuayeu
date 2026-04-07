---
name: project-manager
description: 案件エンティティ CRUD（add/edit/close）。物件識別子・現場番号・エイリアスを対話で収集し、resolver_cli に渡して shards/projects/{Name}/_project.md を生成・更新する。
---

# project-manager

案件マスタデータの登録・編集・クローズを担当する管理スキルです。
メールには断片しか出てこないマスタデータ（物件名、現場番号、得意先紐付け）を、人間対話で確実に収集します。

## 責務

- 新規案件の登録（slug, canonical, aliases, target_path）
- 既存案件のメタデータ編集
- 完工案件のクローズマーキング（archive 発動準備）
- すべての変更を `_alias_resolver.md` に反映

## 対話パターン

新規登録時、AskUserQuestion で以下を順次収集：

1. **案件名（canonical）**: 「○○マンション新築工事」のような正式名称
2. **slug**: ASCII ディレクトリ名（例: `MaruMaruMansion`）。canonical から自動推測してユーザー確認
3. **エイリアス**: 物件略称、現場番号、町名等（カンマ区切り）
4. **得意先**: client シャードの slug を選択（既存リストから）

## CLI 呼び出し

すべて `interfaces.resolver_cli` 経由で永続化します。

### add

```bash
python -m interfaces.resolver_cli add \
  --plugin-root <plugin_root> \
  --kind projects \
  --slug <Slug> \
  --canonical "<正式名称>" \
  --target-path "shards/projects/<Slug>/_project.md" \
  --aliases "<alias1>,<alias2>"
```

### edit

```bash
python -m interfaces.resolver_cli edit \
  --plugin-root <plugin_root> \
  --id projects/<Slug> \
  --canonical "<新名称>" \
  --add-aliases "<追加alias>" \
  --remove-aliases "<削除alias>"
```

### close（論理削除）

```bash
python -m interfaces.resolver_cli remove \
  --plugin-root <plugin_root> \
  --id projects/<Slug>
```

実ファイル移動は `[archive.md](archive.md)` 経由で行います。close は resolver 上の archived フラグのみ立てます。

## 後処理

CLI 成功後、`shards/projects/<Slug>/_project.md` の存在を確認し、無ければ最小テンプレートを作成：

```markdown
# <案件名>

- **現場番号**: <number>
- **得意先**: [[clients/<Client>]]
- **ステータス**: <active|completed>
- **登録日**: <YYYY-MM-DD>

## 概要

(triage / absorb で蓄積されていく)

## 関連

- (空)
```

## エラー対応

- duplicate id → 既存案件への edit を提案
- not found（edit/close 時）→ 既存案件リストを表示
- invalid alias record → ユーザーに入力修正を依頼
