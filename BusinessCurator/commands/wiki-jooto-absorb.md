---
name: wiki-jooto-absorb
description: JootoGrabber が出力した data/jooto/ を MeguruWiki の project shard に吸収する。LLM 判断が本質（board↔project マッピング・タスク要約）なので Python 化しない。
---

# /wiki-jooto-absorb

JootoGrabber（`/jooto-backup`）が `data/jooto/{id}_{slug}/` に出力した
`board.json` / `tasks.json` / `lists.json` / `categories.json` を、
MeguruWiki の対応する `shards/projects/{Slug}/_project.md` に吸収します。

## 動作

このコマンドは Python CLI を呼び出しません。LLM の判断が本質だからです：

- Jooto board ↔ MeguruWiki project のマッピング判定
- タスク群の要約方針（全列挙ではなく「追うべき状態」の抽出）
- 既存記述との整合（重複・矛盾の解消）

方針スキル: [jooto-absorb.md](../skills/wiki/jooto-absorb.md)

## 使用例

```text
/wiki-jooto-absorb                       # data/jooto/ 配下の全 board を処理
/wiki-jooto-absorb 1287379               # 単一 board を処理
/wiki-jooto-absorb --dry-run             # 変更差分の提示のみ（書き込まない）
```

## 前提

1. 運用 wiki インスタンス側 `docs/JOOTO_SCHEMA.md` の仕様に従う（インスタンス側で管理、本プラグインには同梱しない）
2. `JootoGrabber/data/jooto/` が最新化されている（未取得なら `/jooto-backup --all-active` を先に）
3. `_alias_resolver.md` に board 名が alias として載っていると自動解決精度が高い

## 関連

- [jooto-absorb.md](../skills/wiki/jooto-absorb.md)
- JOOTO_SCHEMA.md — 運用 wiki インスタンス側 `docs/` で管理
- `/jooto-backup`: 前段（JootoGrabber）
- `/wiki-absorb`: メール吸収（別経路）
