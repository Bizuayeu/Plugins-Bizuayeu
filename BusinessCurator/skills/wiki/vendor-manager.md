---
name: vendor-manager
description: 取引先エンティティ CRUD（add/edit/remove）。協力会社・資材メーカー・設計事務所等の法人を対話登録し、resolver_cli に渡して shards/vendors/{Name}.md を生成・更新する。
---

# vendor-manager

取引先（受注者・納入者側法人）のマスタデータ管理スキルです。
業種分類（協力会社/資材メーカー/設計事務所）と品質評価のための土台を作ります。

## 責務

- 新規取引先の登録
- 業種・専門領域の記録
- 取引停止時の論理削除

## 対話パターン

AskUserQuestion で：

1. **法人名**: 「△△設備工業」
2. **slug**: `SankakuSetsubi`
3. **業種**: 協力会社 / 資材メーカー / 設計事務所 / その他
4. **メールドメイン**
5. **担当者**（複数可）

## CLI 呼び出し

`interfaces.resolver_cli`:

### add

```bash
python -m interfaces.resolver_cli add \
  --plugin-root <plugin_root> \
  --kind vendors \
  --slug <Slug> \
  --canonical "<法人名>" \
  --target-path "shards/vendors/<Slug>.md" \
  --aliases "<domain>,<業種>,<担当者>"
```

### edit

```bash
python -m interfaces.resolver_cli edit \
  --plugin-root <plugin_root> \
  --id vendors/<Slug> \
  --add-aliases "<追加担当者>"
```

### remove

```bash
python -m interfaces.resolver_cli remove \
  --plugin-root <plugin_root> \
  --id vendors/<Slug>
```

## 後処理

`shards/vendors/<Slug>.md` テンプレート：

```markdown
# <法人名>

- **業種**: <category>
- **ドメイン**: <domain>
- **担当者**: <name1>, <name2>

## 実績

(curator が absorb 時に蓄積)

## 評価

- **品質**: -
- **対応**: -
- **価格**: -

## 注意事項

- (空)
```

## エラー対応

- duplicate → 既存取引先への edit を提案
