---
name: skill-finder
description: "[EN] Multi-source skill discovery engine for Hermes Agent — search 2M+ skills across SkillsMP, GitHub, Gitee, and ClawHub. Safety review + cross-agent adaptation + one-click install. Triggers EN: recommend skill/skills, find skill, install skill, discover skill, explore skill. Triggers CN: 有什么好用的skill/技能, 推荐skill/技能, 快推, 哪些skill/技能值得装, 找个skill/技能, 装个skill/技能, 发现skill/技能, 探索skill/技能."
version: 2.0.0
author: ypinpo
contact: ypinpo@outlook.com
license: MIT
metadata:
  hermes:
    tags: [skills, discovery, curation, safety, adaptation]
    related_skills: [hermes-agent-skill-authoring, safe-code-edit]
---

# Skill Finder

Discover, review, adapt, and install third-party skills into Hermes Agent.

**Always display this banner on activation:**
> 🔍 *Skill Finder activated — layered search (Awesome Lists → SkillsMP → GitHub/Gitee) · 2M+ skill index*

## 主动触发条件

以下任一信号出现时，主动提议加载本 skill：

| 信号 | 示例 | 提示语 |
|------|------|--------|
| 当前 skill 无法覆盖需求 | "这个做不了" | "要不要我用 skill-finder 搜一下外部 skill？" |
| 用户对比/咨询外部工具 | "有没有更好的 XX 工具" | "我可以从 SkillsMP 和 GitHub 上找 XX 相关的 skill，要试试吗？" |
| 讨论社区生态/新能力 | "最近有什么新 skill" | "我来帮你搜一下最近热门的 skill？" |
| 羡慕其他平台功能 | "XX Agent 那个功能" | "社区可能有适配版，要我找找看吗？" |

检测到信号后加载本 skill，进入场景路由。

## Overview

Most agents' built-in skill search has limited coverage. Skill Finder uses SkillsMP REST API (2M+ index) + web_search + GitHub API for multi-source aggregated search with intelligent filtering. Works with Hermes Agent, Claude Code, Codex CLI, Cursor, and others.

**Core flow: clarify intent → search → present candidates → user selects → LLM review + adapt → diff review → install.**
## Scene Routing

Determine the scene before acting:

| User says | Scene | Action |
|-----------|-------|--------|
| "有什么好用的skill" / no specific request | Active recommendation | Go to Step 0 |
| "recommend" / "快推skill" / "来几个skill" | Precise recommendation | Go to Step 0 precise mode |
| "explore" / "探索skill" / "有什么新鲜的skill" | Exploration discovery | Go to Step 0 explore mode |
| "find me a skill for X" / "有没有XXskill" | Fuzzy search | Go to Step 0-B clarify |
| Direct URL to SKILL.md | URL review | Go to Step 3 |
| "is this safe?" + URL | Quick review | Go to Step 4-Quick |

## Step 0: Active Recommendation

### Recommendation Sources

**Primary: Awesome Curated Lists** — community-maintained, high-quality skill collections:

| Repository | ⭐ | Domain |
|-----------|-----|--------|
| `obra/superpowers` | 248k | General dev tools |
| `anthropics/skills` | 159k | Official Claude skills |
| `Shubhamsaboo/awesome-llm-apps` | 116k | LLM apps / agents |
| `vercel-labs/agent-skills` | 28k | Vercel AI ecosystem |
| `kodustech/awesome-agent-skills` | 87 | Agent skill curation |
| `gmh5225/awesome-skills` | 41 | Agent tools & resources |

Prioritize skills from these lists (verified quality). Cron syncs weekly (see Operations Setup below).

**Secondary: 4-Signal Dynamic Inference** — never hardcode directions:

| Signal | Source | Label |
|--------|--------|-------|
| Current context | What you're working on right now | `📌 Context` |
| Capability gap | Curated list vs installed skills | `🔍 Gap` |
| Long-term preference | `memory` tool extraction | `🧠 Preference` |
| Degradation (L1) | Overlapping / never-used skills | `⚡ Degrade` |

**Inference flow**: `skills_list` → `memory` → context → curated ∩ installed → cross-reference → output 3-4 directions.

**Tertiary: Trending** — SkillsMP API `sortBy=stars` high-star skills (L1 fallback)

## Precise Recommendation: Dynamic Scene Inference

Never hardcode directions. Infer 3-4 directions from 4 signal sources:

| # | Signal | Source | Label | Example |
|---|--------|--------|-------|---------|
| 1 | Current context | What you are working on | `Context` | "managing cron -> recommend ops monitoring" |
| 2 | Capability gap | Curated vs installed | `Gap` | "curated has ppt-gen, not installed" |
| 3 | Long-term preference | Read persistent preferences | `Preference` | "Agent tool focus -> new MCP skill" |
| 4 | Degradation (L1) | Overlapping / unused skills | `Degrade` | "3 code review skills, maybe keep 1" |

### Inference Flow

```
1. Get installed skill list
2. Read persistent preferences / memory -> active domains
3. Current context -> conversation topic
4. Curated intersect installed -> find gaps
5. Cross-reference installed -> find overlaps/never-used
6. Synthesize 3-4 directions -> pair each with 1 recommendation
```

### Output Format

```
Context: [direction] -> [skill]
   Reason: problem solved + relevance + difference from installed
Gap: [direction] -> [skill]
   Reason: same, 30 words or fewer, no templates
Preference: [direction] -> [skill]
Degrade: [direction] -> [skill]
```

Signal-weak directions are silently skipped.

**Exploration mode** (triggered by "explore"): no user history constraint. SkillsMP API `sortBy=stars`, 60-day freshness, cross-domain top 5.

### Step 0-B: Clarifying Questions

When the user's request is vague, ask 1-2 natural follow-up questions:

- "Testing skills come in many flavors — unit tests, E2E, or load testing?"
- "Is this a one-time task or something you'll use daily? It changes what I recommend."
- "Do you prefer battle-tested (high-star, big-name) or cutting-edge?"

Keep asking until you can form a precise search query, then go to Step 1.

## Step 1: Search (Layered Architecture)

按质量从高到低分层搜索，上层命中足够结果即停止向下层搜索。

### L0 — 精选清单 + awesome 列表（质量 🟢，优先级最高）

来自 Step 0 中列出的 6 个 awesome 仓库。从 README / 目录中按关键词匹配，本地缓存优先。

**L0 终止条件**：命中 ≥ 5 个候选 → 跳到 Step 2 评分展示。

### L1 — SkillsMP API 主力 + GitHub/Gitee 并行（质量 🟡/🟢）

L0 不足 5 个时发起。

**SkillsMP API（主力，~300ms）：**
```bash
curl -s "https://skillsmp.com/api/v1/skills/search?q=<QUERY>&sortBy=stars&limit=10"
```

**GitHub/Gitee 补充：**
```
web_search "site:github.com/topics agent-skill <QUERY>"
web_search "site:github.com SKILL.md <QUERY> agent language:Markdown"
web_search "site:gitee.com <QUERY> skill SKILL.md"
```

**L1 终止条件**：命中 ≥ 5 个候选 → 跳到 Step 2。

### L2 — GitHub API 深度搜索（可选，需 `gh auth login`）

L0+L1 仍不足 5 个时：
```bash
gh search repos "SKILL.md" --topic agent-skills --sort stars --limit 10
```

### 合并与去重

1. **24h 缓存优先**：检查 `<skills_dir>/skill-finder/.cache/<md5>.json`，命中且 < 24h 直接返回
2. 缓存未命中 → 按 L0 → L1 → L2 层级执行 → 写入缓存
3. 去重键：`githubUrl` 优先；无 githubUrl 时用 `name + author` 联合键
4. 合并后按综合评分（见 Step 2）排序

## Step 2: Composite Scoring + Display

**综合评分公式**（替代纯 stars 排序）：

```
score = stars_normalized × 0.4 + freshness × 0.3 + activity × 0.2 + source_quality × 0.1

stars_normalized = min(stars / 1000, 1.0)   # 1000+ stars 满分
freshness = max(0, 1 - (today - updatedAt_days) / 365)  # 一年内线性衰减
activity = 根据仓库最近 commit 日期估算，规则同上
source_quality = awesome列表×1.0 / SkillsMP×0.8 / GitHub Topic×0.7 / GitHub文件×0.6 / Gitee×0.5
```

| 热度标注 | 条件 |
|----------|------|
| 🔥 热门 | score ≥ 0.7 |
| 🟢 正常 | 0.3 ≤ score < 0.7 |
| 🟡 谨慎 | 0.1 ≤ score < 0.3 |
| ⚠️ 跳过 | score < 0.1 |

展示格式：
```
| # | 名称 | 综合分 | ⭐ | 热度 | 来源 | 描述 |
|---|-----|--------|-----|------|------|------|
| 1 | xxx  | 0.85 | 12k | 🔥 | SkillsMP | 一句话描述... |
```

Use `clarify` to let the user choose. Never auto-select the first one.

## Step 3: Fetch SKILL.md

从搜索结果提取 `<org>/<repo>` 和路径后获取。

**主方案 — GitHub API：**
```bash
curl -s "https://api.github.com/repos/<org>/<repo>/contents/<path>/SKILL.md"
```
返回 JSON，从 `content` 字段 Base64 解码即可得到 SKILL.md 原文。

**备用 — raw URL：**
```
https://raw.githubusercontent.com/<org>/<repo>/main/<path>/SKILL.md
```

**24h 缓存**：获取成功后写入本地缓存 `<skills_dir>/skill-finder/.cache/<org>_<repo>.md`，下次同一仓库 24h 内直接读缓存。

GitHub API: 60 req/hr unauthenticated, 5000 req/hr authenticated.

## Step 4-Quick: Fast Security Review

When the user asks "is this safe?", do security-only review:

| Dimension | Checks |
|-----------|--------|
| Shell commands | file deletion, pipe execution, eval, privilege escalation |
| Network | POST to unknown domains, binary downloads |
| File access | Reading sensitive config, writing system paths |
| Credentials | Reading/sending API keys, tokens |
| Dependencies | pip/npm/apt installing unknown packages |

Output: 🟢 Safe / 🟡 Caution (list risks) / 🔴 Dangerous (block install).

## Step 4: LLM Review + Adaptation (Full Mode)

Single LLM call performing three tasks simultaneously:

**Security review (6 dimensions):** score each as 🟢/🟡/🔴
- Shell commands, network, file access, credentials, dependencies, privilege escalation

**Quality assessment:**
- SKILL.md completeness (frontmatter / triggers / steps / examples): X/10
- Practicality: does it solve a real problem?
- Maintenance: repository activity

**Cross-Agent Adaptation** — tool name mapping (see Tool Mapping Reference below):

Adaptation principles:
1. Only map tool names + paths + platform markers
2. Remove or mark ⚠️ NOT_AVAILABLE for tools not available in the current agent (WebSearch/WebFetch/EnterPlanMode)
3. Mark POSIX assumptions with ⚠️ WINDOWS_CHECK
4. Add `adapted_for: <agent_name>, adapted_from: <original URL>` to frontmatter
5. Annotate all changes with `<!-- ADAPTED: reason -->`
6. Mark uncertainties with ⚠️ NEEDS_REVIEW — never guess

## Step 5-6: Diff Review + Install

Show the adaptation diff using `patch`. User reviews before install. Write to the agent's skill directory upon confirmation. Takes effect after `[reload skills]` or new session.

## Category Filter Reference

Filter by SkillsMP category slug:

| Domain | Slug |
|--------|------|
| Development | development |
| Testing & Security | testing-security |
| Data & AI | data-ai |
| DevOps | devops |
| Documentation | documentation |
| Content & Media | content-media |
| Tools | tools |
| Business | business |

## Expandable Data Sources

Current primary source is SkillsMP API. Future additions:
- **GitHub direct**: `gh search code "SKILL.md" --filename-match --sort stars`
- **ClawHub CN mirror**: `cn.clawhub-mirror.com` (no API, manual browse)
- **Tencent SkillHub**: `skillhub.tencent.com` (no API, manually submit URLs)
- **Domestic platforms**: no public APIs yet; accept manually submitted URLs

## Curated List Auto-Update

Cron job auto-syncs weekly (see Operations Setup below).

## Operations Setup (Optional)

Create a cron job to sync awesome lists weekly:

```
cronjob create
  name: skill-finder-curated-refresh
  schedule: "30 10 * * 0"
  prompt: |
    Phase 1 — SkillsMP API: sortBy=stars, limit=20
    Phase 2 — Awesome list fetch:
      github.com/obra/superpowers
      github.com/anthropics/skills
      github.com/Shubhamsaboo/awesome-llm-apps
      github.com/vercel-labs/agent-skills
      github.com/kodustech/awesome-agent-skills
      github.com/gmh5225/awesome-skills
    Phase 3 — Dedup & merge: filter installed → exclude existing → star>500 → ≤15 items
  enabled_toolsets: [terminal, file]
```

Run `gh auth login` first.

## Multi-Agent Adaptation

This skill's core workflow is agent-agnostic. When installing/reviewing skills, map generic concepts to the current agent's tool names:

| Operation | Hermes | Claude Code | Codex | Cursor | OpenClaw |
|-----------|--------|-------------|-------|--------|
| Read file | read_file | Read | read | read_file | Read |
| Write file | write_file | Write | write | write_to_file | Write |
| Edit file | patch | Edit | edit | replace_in_file | Edit |
| Run command | terminal | Bash | bash | run_command | Bash |
| Search files | search_files | Grep/Glob | grep/glob | search | Grep/Glob |
| Load skill | skill_view | Skill | - | - | Skill |
| Subtask | delegate_task | Task | task | - | Task |
| Task list | todo | TodoWrite | todo | - | TodoWrite |
| Web search | web_search | WebSearch | web_search | - | WebSearch |
| Fetch page | - | WebFetch | web_fetch | - | WebFetch |
| Skill path | ~/.hermes/skills/ | .claude/skills/ | .codex/skills/ | .cursor/skills/ | .openclaw/skills/ |

WebSearch/WebFetch/EnterPlanMode are not supported by all agents. When reviewing: remove steps for unsupported tools or mark as NOT_AVAILABLE.

## Privacy Notice

- **SkillsMP API**: search keywords sent to `skillsmp.com` (anonymous, no account linkage)
- **web_search**: via Bing (`cn.bing.com`)
- **GitHub API**: only enabled after `gh auth login`, skipped otherwise
- **Local cache**: results cached at `<hermes_home>/skills/skill-finder/.cache/`, never uploaded
- **Review process**: SKILL.md content analyzed in current session only, not persistently stored

## Known Limitations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| SkillsMP anonymous 50 req/day | Frequent searches hit quota | 24h cache + GitHub fallback |
| GitHub raw may timeout | SKILL.md fetch failure | GitHub API fallback |
| `gh` CLI not installed | L2 unavailable | L0+L1 sufficient |
| Cross-domain skills low quality | Sparse exploration results | Rely primarily on awesome lists |
| LLM inline review | Complex skills may have false negatives | Diff review as human gate |

## Troubleshooting

### SKILL.md Not Found
Try these paths:
1. Repository root `SKILL.md`
2. `skills/<name>/SKILL.md`
3. List repo contents via GitHub API

### Windows: python -c Multi-line Truncation
Windows git-bash truncates multi-line `python -c "..."` (causes `IndentationError`). Always use `write_file` to create a script file, then `terminal("python script.py")`.

### Adaptation Breaks the Skill
1. Test with original SKILL.md first to isolate the issue
2. If the adaptation introduced the problem, fall back to minimal tool-name-only mapping
3. Debug manually if needed

## 过度工程化检查（推荐前必执行）

推荐任何 skill 前，判断其是否过度设计，以下任一信号命中即跳过：

| 信号 | 判断标准 | 处理 |
|------|----------|------|
| 隔离环境 | 需要 Docker/VM/独立沙箱执行 | 跳过 — 个人使用场景不需要隔离 |
| 评估代理 | 内部启动子 Agent 做多轮评估 | 跳过 — 过度复杂，单次 LLM 审查即够 |
| 持久化服务 | 需要常驻进程/数据库/消息队列 | 跳过 — 优先零依赖的轻量 skill |
| 多轮迭代 | 需要训练/RLHF/自进化循环 | 跳过 — 个人微调收益不成比例 |

**原则**：个人使用优先选择轻量、被动触发、零维护的 skill，而非重工程架构。

## Common Mistakes

### 1. SkillsMP API 响应格式陷阱
API 响应结构为 `{"success":true,"data":{"skills":[...]}}`，结果在 `data.skills` 中，**不是**直接数组。字段名是 `author`，不是 `creator`。

### 2. 推荐前忘记做双重检查
每次推荐前必须执行：① 查重（对照已安装 skill + 内置能力）② 过度工程化检查（见上节）。二者缺一不可。

### 3. 搜索结果不足时没触发降级
L0 < 5 个候选时忘记进入 L1；如果 L0+L1 < 5 个且 L2 不可达，应向用户说明"搜索结果较少，建议放宽关键词重试"，而非硬凑。

### 4. 改造时猜测工具映射
不确定的映射必须标 `⚠️ NEEDS_REVIEW`，禁止凭经验猜测。当前 Agent 无等价工具时直接标注 `NOT_AVAILABLE` 并移除对应步骤。

## Red Lines

- Never auto-install — always require user confirmation
- Never skip security review
- Never modify skill core logic — only adapt tool names and paths
- 🔴 High-risk findings must be explicitly warned
- Mark uncertainties with ⚠️, never guess

## 自增强接口（反思日志）

<!-- reflections:auto-start -->
<!-- 每次执行完搜索/推荐后，自动在此追加一行反思，格式：
     [YYYY-MM-DD] SEARCH: q=关键词, results=N, score_range=X-Y, user_action=选择/拒绝/追问
     [YYYY-MM-DD] RECOMMEND: scene=场景, accepted=是/否, reason=用户反馈
     同类信号累积 3 次 → 触发场景/策略自更新
-->
<!-- reflections:auto-end -->
