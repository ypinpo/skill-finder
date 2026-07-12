# Skill Finder

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.10.0-green.svg)]()

Multi-source skill discovery engine for AI agents — search **2M+ skills**, automated safety review, cross-agent adaptation, one-click install.

> 🔍 Works with: **Hermes Agent · Claude Code · Codex CLI · Cursor · OpenClaw**

## Keywords / 触发词

| English | 中文 |
|---------|------|
| recommend skill/skills, find skill, install skill, discover skill, explore skill | 推荐skill/技能, 找个skill/技能, 装个skill/技能, 发现skill/技能, 探索skill/技能 |

## Features

- **Layered search** — L0 Awesome Lists → L1 SkillsMP + GitHub/Gitee → L2 GitHub API, upper tier hits stop early
- **Composite scoring** — stars × 0.4 + freshness × 0.3 + activity × 0.2 + source quality × 0.1, not just stars
- **Smart recommendations** — 4-signal dynamic inference (context/gap/preference/degradation) + proactive trigger detection
- **Safety review** — 6-dimension automated audit before install + over-engineering gate
- **Cross-agent adaptation** — auto-map tool names for Hermes, Claude Code, Codex, Cursor
- **Curated lists** — 8 awesome repos with weekly auto-sync
- **24h cache** — repeat queries return instantly
- **Self-improving** — reflection log tracks recommendation outcomes, auto-tunes strategy

## Quick Start

| You say | What happens |
|---------|-------------|
| 推荐 / recommend | Smart recommendations based on your context |
| 帮我找 XX 的 skill | Multi-source search across 2M+ skills |
| 探索 / explore | Cross-domain trending discovery with layered search (L0→L1→L2), composite scoring, and proactive trigger detection |
| 这个 SKILL.md 安全吗？ | Quick security audit (6-dimension scan) |
| 装这个 skill | Full review → adaptation → diff review → install |

## Install

```bash
# Hermes Agent
hermes skills install https://raw.githubusercontent.com/ypinpo/hermes-skills/main/skill-finder/SKILL.md

# Claude Code
/skill https://raw.githubusercontent.com/ypinpo/hermes-skills/main/skill-finder/SKILL.md

# Codex / Cursor
# Load SKILL.md directly in your IDE
```

## Supported Agents

| Agent | Tool Mapping | Skill Path |
|-------|-------------|------------|
| Hermes Agent | Native | `~/.hermes/skills/` |
| Claude Code | Full | `.claude/skills/` |
| Codex CLI | Full | `.codex/skills/` |
| Cursor | Full | `.cursor/skills/` |
| OpenClaw | Full | `.openclaw/skills/` |

## Data Sources

| Source | Type | Size |
|--------|------|------|
| SkillsMP API | Primary | 2M+ indexed SKILL.md |
| GitHub Search | Parallel | Unlimited (topic filter) |
| Gitee | Domestic | Chinese skill ecosystem |
| ClawHub Mirror | Chinese | OpenClaw skills |

**Curated awesome lists** (weekly auto-sync):

| Repository | Stars | Domain |
|-----------|-------|--------|
| [obra/superpowers](https://github.com/obra/superpowers) | 248k | General dev tools |
| [anthropics/skills](https://github.com/anthropics/skills) | 159k | Official Claude skills |
| [Shubhamsaboo/awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) | 116k | LLM apps / agents |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | 28k | Vercel AI ecosystem |
| [heilcheng/awesome-agent-skills](https://github.com/heilcheng/awesome-agent-skills) | 6k | Agent skill aggregation 🆕 |
| [codesstar/hermes-skill-atlas](https://github.com/codesstar/hermes-skill-atlas) | — | Hermes 专用 70+ skill 浏览器 🆕 |
| [kodustech/awesome-agent-skills](https://github.com/kodustech/awesome-agent-skills) | 87 | Agent skill curation |
| [gmh5225/awesome-skills](https://github.com/gmh5225/awesome-skills) | 41 | Agent tools & resources |

## Verify

After install, say `推荐` or `recommend` in a new session. You should see 4-signal dynamic recommendations. If not, run `/reload-skills`.

## License

Orchestration logic, review templates, and adaptation code: **MIT**.
Third-party skill indices, API data, and tool names: copyright of respective authors/platforms.
Awesome list content: copyright of original authors. This project serves for aggregation and discovery only.

## Author

ypinpo — ypinpo@outlook.com
