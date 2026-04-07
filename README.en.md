English | [日本語](README.md)

# Plugins-Bizuayeu

Claude Code plugins for SMB owners and field practitioners

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Why Plugins-Bizuayeu?

Extends Claude Code from a "coding tool" into a "knowledgeable collaborator for management and operations."
While its sister repository [Plugins-Weave](https://github.com/Bizuayeu/Plugins-Weave) handles the
**ontological expansion of autonomous AI** (long-term memory, agency, emotional expression),
Plugins-Bizuayeu serves as **the extension of a practitioner's hand**.

| Challenge | Solution | Plugin |
|-----------|----------|--------|
| **B2B email knowledge gets lost** | Weaves projects, clients, vendors, and know-how into a 4-shard wiki | BusinessCurator |

---

## Plugins

### BusinessCurator

**Enterprise Business Email Knowledge Management Plugin**

An enterprise extension of Karpathy-style personal wiki, weaving business emails
into a structured wiki across 4 shards (projects / clients / vendors / knowledge).

> *writer, not filing clerk* — Don't ask where to file facts;
> ask what they mean and how they connect to existing understanding.

#### Key Features

- **4 fixed shards**: projects / clients / vendors / knowledge
- **Two-layer structure**: humans define masters (manager), AI operates them (curator)
- **Rule-first triage**: 80% resolved by rules, 20% by LLM
- **md / Python separation**: mechanical processing in Python, judgment and dialogue in md
- **Clean Architecture × TDD**: 589 tests / 95.08% coverage / mypy strict 0 errors

#### Main Commands (20 total)

| Category | Representative Commands | Purpose |
|---|---|---|
| Manager | `/wiki-project-add` `/wiki-client-add` `/wiki-vendor-add` | Master data CRUD |
| Operation | `/wiki-ingest` `/wiki-triage` `/wiki-absorb` `/wiki-archive` | Ingest → triage → absorb → archive |
| Auxiliary | `/wiki-query` `/wiki-status` | Cross-shard query / metrics |

→ See [BusinessCurator/README.md](BusinessCurator/README.md) for details

---

## Quick Installation

### 1. Add Marketplace

```ClaudeCLI
/marketplace add https://github.com/Bizuayeu/Plugins-Bizuayeu
```

### 2. Install Plugin

```ClaudeCLI
/plugin install BusinessCurator@Plugins-Bizuayeu
```

---

## License

**MIT License** - See [LICENSE](LICENSE) for details

---

## Related Repository

- [Plugins-Weave](https://github.com/Bizuayeu/Plugins-Weave) — Claude Code plugins for autonomous AI with long-term memory, expression, and communication

---

**Plugins-Bizuayeu** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Bizuayeu)
