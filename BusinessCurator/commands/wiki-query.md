---
name: wiki-query
description: wiki 横断質問応答。alias resolver でエンティティを特定し、関連シャードの記事を読んで答える。
---

# /wiki-query

BusinessCurator wiki に質問します。

## 動作

このコマンドは Python CLI を呼び出しません。読解と統合は LLM の本質的役割です。

エンティティの名寄せは `_alias_resolver.md` にあります。ここで質問中の固有名を特定してから該当シャードの記事へ入り、答えに足りるところまで wikilink を辿ってください。

## 使用例

```text
/wiki-query 排煙設備で問題があった案件は？
/wiki-query □□不動産との取引履歴を教えて
/wiki-query △△設備工業の評価は？
```

## ルール

- `inbox/raw-entries/` は読まない（生メールは知識ベースではない）
- 推測しない。wiki にない情報は「該当なし」と答える
- wiki ファイルは変更しない（query は read-only）

## 関連

- [SKILL.md](../skills/wiki/SKILL.md): 全体ナビゲーション
- `/wiki-status`: メトリクス確認
