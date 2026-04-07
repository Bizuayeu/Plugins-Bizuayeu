---
name: wiki-absorb
description: triage 済みエントリを各シャード wiki に吸収する。シャード別 curator スキル方針に従う。LLM の判断が本質なので Python 化しない。
---

# /wiki-absorb

triage 済みエントリをシャード wiki に編み込みます。

## 動作

このコマンドは Python CLI を呼び出しません。LLM の判断が本質だからです。

シャード別の方針スキルを Claude が直接読んで実行します：

- `projects`: [project-curator.md](../skills/wiki/project-curator.md)
- `clients`: [client-curator.md](../skills/wiki/client-curator.md)
- `vendors`: [vendor-curator.md](../skills/wiki/vendor-curator.md)
- `knowledge`: [knowledge-curator.md](../skills/wiki/knowledge-curator.md)

## 使用例

```text
/wiki-absorb projects                # 案件シャードのみ
/wiki-absorb projects last-30-days   # 直近30日のみ
/wiki-absorb all                     # 全シャード
```

## 共通原則

`[../../../.claude/skills/wiki/SKILL.md](../../../.claude/skills/wiki/SKILL.md)` の **writer, not filing clerk** 原則を継承：

- 事実をどこに置くかではなく、それが何を意味するかを問う
- 既存記事に append するのではなく、新たな次元を見出して統合する
- 事象（diary-driven）ではなく、テーマ（narrative-driven）で記事を構造化する

## 関連

- [project-curator.md](../skills/wiki/project-curator.md)
- `/wiki-triage`: 前段
- `/wiki-archive`: 完工後の卒業プロセス
