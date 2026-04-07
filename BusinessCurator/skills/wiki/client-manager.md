---
name: client-manager
description: 得意先エンティティ CRUD（add/edit/remove）。法人名・ドメイン・キーパーソン・与信メモを対話で収集し、resolver_cli に渡して shards/clients/{Name}.md を生成・更新する。
---

# client-manager

得意先（発注者側法人）のマスタデータ管理スキルです。
案件を跨いで関係が継続する主体なので、ドメインベースの triage を効かせるための情報収集を重視します。

## 責務

- 新規得意先の登録（slug, canonical, aliases, ドメイン）
- 既存得意先の編集（キーパーソン追加、ドメイン変更）
- 取引終了時の論理削除（archived フラグ）

## 対話パターン

新規登録時に AskUserQuestion で：

1. **法人名（canonical）**: 「株式会社□□不動産」
2. **slug**: `ShikakuFudosan` 等の ASCII（自動推測 + ユーザー確認）
3. **メールドメイン**: `shikaku.co.jp` 等。triage の from ベース判定に使用
4. **エイリアス**: 略称、担当者名等

ドメインは aliases に含めることで triage_cli が自動でルール化します。

## CLI 呼び出し

すべて `interfaces.resolver_cli` 経由。

### add

```bash
python -m interfaces.resolver_cli add \
  --plugin-root <plugin_root> \
  --kind clients \
  --slug <Slug> \
  --canonical "<法人名>" \
  --target-path "shards/clients/<Slug>.md" \
  --aliases "<domain>,<略称>"
```

### edit

```bash
python -m interfaces.resolver_cli edit \
  --plugin-root <plugin_root> \
  --id clients/<Slug> \
  --add-aliases "<新キーパーソン>"
```

### remove

```bash
python -m interfaces.resolver_cli remove \
  --plugin-root <plugin_root> \
  --id clients/<Slug>
```

## 後処理

`shards/clients/<Slug>.md` のテンプレート：

```markdown
# <法人名>

- **ドメイン**: <domain>
- **エイリアス**: also: <略称>, <担当者>
- **登録日**: <YYYY-MM-DD>

## 関係性

(curator が更新)

## キーパーソン

- (空)

## 取引履歴

(absorb で蓄積)
```

## エラー対応

- duplicate → 既存得意先への edit を提案
- not found → list 表示
