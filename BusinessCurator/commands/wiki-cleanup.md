---
name: wiki-cleanup
description: 既存記事の品質改善（diary-driven 構造の修正、bloated/stub の整理、broken wikilink の修復）。Python CLI を呼ばず、curator スキルが直接実行する。
---

# /wiki-cleanup

既存 wiki 記事の品質を監査・改善します。

## 動作

このコマンドは Python CLI を呼びません。LLM の判断が本質です。

シャード別の curator スキルを Claude が直接読んで実行：

- `projects`: [project-curator.md](../skills/wiki/project-curator.md)
- `clients`: [client-curator.md](../skills/wiki/client-curator.md)
- `vendors`: [vendor-curator.md](../skills/wiki/vendor-curator.md)
- `knowledge`: [knowledge-curator.md](../skills/wiki/knowledge-curator.md)

## 使用例

```text
/wiki-cleanup projects        # 案件シャードのみ
/wiki-cleanup all             # 全シャード
```

## 監査項目

既存記事を次の 5 点で監査します：

1. **構造**: diary-driven か narrative-driven か
2. **行数**: bloated (>120 lines) / stub (<15 lines)
3. **トーン**: フラットすぎないか、漂白されていないか
4. **wikilink**: broken link がないか、欠落 link がないか
5. **クロスシャード参照**: 案件 ↔ 得意先 ↔ 取引先 ↔ 知見 が繋がっているか

## 関連

- `/wiki-absorb`: 新規吸収（cleanup と方針スキルを共有）
