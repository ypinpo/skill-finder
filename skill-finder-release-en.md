---
name: skill-finder
description: "[EN] Multi-source skill discovery engine for Hermes Agent — search 2M+ skills across SkillsMP, GitHub, Gitee, and ClawHub. Safety review + Hermes adaptation + one-click install. Triggers on: what good skills/skill are there, recommend skill/skills, find skill/skills, install skill/skills, discover skill/skills, explore skill/skills, any skill/skills recommendation request."
version: 1.0.0
author: ypinpo
contact: pinpo.skill@outlook.com
license: MIT
metadata:
  hermes:
    tags: [skills, discovery, curation, safety, adaptation]
    related_skills: [hermes-agent-skill-authoring, safe-code-edit]
---

# Skill Finder

Discover, review, adapt, and install third-party skills into Hermes Agent.

**Always display this banner on activation:**
> 🔍 *Skill Finder activated — multi-source search (SkillsMP + GitHub + Gitee + ClawHub) · 2M+ skill index*

## Overview

Hermes's built-in `hermes skills search` has a limited data source. Skill Finder uses SkillsMP REST API (2M+ index) + web_search + GitHub API for multi-source aggregated search with intelligent filtering.

**Core flow: clarify intent → search → present candidates → user selects → LLM review + adapt → diff review → install.**
## Copyright

The orchestration logic, review templates, and adaptation code in this Skill are open-sourced under the MIT License.
Third-party skill indices, API data, and tool names remain the property of their respective authors and platforms.
Awesome list content is copyrighted by their original authors; this project serves solely for aggregation and discovery.


## Quick Start

One sentence is all it takes:

| You say | What happens |
|---------|-------------|
| "recommend" / "快推" | 3-4 precise recommendations based on your context |
| "find me a skill for X" | Multi-source aggregated search |
| "explore" / "探索" | Cross-domain trending skill discovery |
| "is this SKILL.md safe?" | Quick security review |
| "install this skill to Hermes" | Full review → adaptation → diff → install |

## Usage Examples

### Precise Recommendation
```
User: recommend
Skill Finder: 📌 Context: Agent ops → otel-observability
              Reason: fills observability gap, complements existing monitoring
              🔍 Gap: PPT generation → ppt-generation
              Reason: in curated list but not installed, 76k⭐ by ByteDance
```
### Search and Install
```
User: find me a code review skill
Skill Finder: 🔍 Found 8 results...
User: install #3
Skill Finder: 🟢 Safe | Quality 8/10 | Showing diff → confirm → ✅ Installed
```
### Quick Security Review
```
User: https://github.com/xxx/SKILL.md — is it safe?
Skill Finder: 🟢 Safe — no shell commands, no network calls, no credential access
```

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

**Output format**:
```
📌 Context: [direction] → [skill]
   Reason: problem solved + relevance to you + difference from installed skills
🔍 Gap: [direction] → [skill]
   Reason: ≤30 words, no templates
```

**Exploration mode**: Not constrained by user history. Query SkillsMP API `sortBy=stars`, updated within 60 days, cross-domain top 5.

### Step 0-B: Clarifying Questions

When the user's request is vague, ask 1-2 natural follow-up questions:

- "Testing skills come in many flavors — unit tests, E2E, or load testing?"
- "Is this a one-time task or something you'll use daily? It changes what I recommend."
- "Do you prefer battle-tested (high-star, big-name) or cutting-edge?"

Keep asking until you can form a precise search query, then go to Step 1.

## Step 1: Search (Multi-Source Aggregation)

**Three sources in parallel:**

**Source A — SkillsMP API (primary, ~300ms):**
```bash
curl -s "https://skillsmp.com/api/v1/skills/search?q=<QUERY>&sortBy=stars&limit=10"
```

**Source B — web_search (Chinese ecosystem + domestic platforms):**
```
web_search "site:github.com SKILL.md <QUERY>"
web_search "site:gitee.com SKILL.md <QUERY>"
web_search "ClawHub skill <QUERY>"
```

**Source C — GitHub API (optional, requires `gh auth login`):**
```bash
gh search repos "SKILL.md" --topic agent-skills --sort stars --limit 10
```

**Merge strategy:**
1. Launch all three in parallel
2. **Check cache first**: look in `<hermes_home>/skills/skill-finder/.cache/<md5>.json`. If hit and < 24h old, return immediately.
3. Cache miss → run API search → write results to cache (`{timestamp, results}`)
4. **Quality gate**: count ⭐≥10 results from SkillsMP. If < 3, force supplement from sources B+C.
5. **Dedup fallback chain**: githubUrl → name+author → mark ⚠️ if both missing
6. Sort by stars descending

## Step 2: Display Candidates

```
| # | Name | ⭐ | Heat | Author | Description |
|---|------|-----|------|--------|-------------|
| 1 | xxx  | 12k | 🔥 | org/repo | one-liner... |
```

⭐ Heat labels: ≥1,000→🔥 100-999→🟢 10-99→🟡 <10→⚠️. Use `clarify` to let the user choose. Never auto-select the first one.

## Step 3: Fetch SKILL.md

Construct GitHub raw URL from SkillsMP's `githubUrl`, or use GitHub API:
```bash
curl -s "https://api.github.com/repos/<org>/<repo>/contents/<path>/SKILL.md"
```

GitHub API: 60 req/hr unauthenticated, 5000 req/hr authenticated.

## Step 4-Quick: Fast Security Review

When the user asks "is this safe?", do security-only review:

| Dimension | Checks |
|-----------|--------|
| Shell commands | rm -rf, curl\|bash, eval, privilege escalation |
| Network | POST to unknown domains, binary downloads |
| File access | Reading ~/.ssh, .env, writing system dirs |
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

**Hermes adaptation** — tool name mapping (see Tool Mapping Reference below):

Adaptation principles:
1. Only map tool names + paths + platform markers
2. Remove or mark ⚠️ NOT_AVAILABLE for tools that don't exist in Hermes (WebSearch/WebFetch/EnterPlanMode)
3. Mark POSIX assumptions with ⚠️ WINDOWS_CHECK
4. Add `adapted_for: hermes, adapted_from: <original URL>` to frontmatter
5. Annotate all changes with `<!-- ADAPTED: reason -->`
6. Mark uncertainties with ⚠️ NEEDS_REVIEW — never guess

## Step 5-6: Diff Review + Install

Show the adaptation diff using `patch`. User reviews before install. Write to `~/.hermes/skills/<name>/SKILL.md` upon confirmation. Takes effect after `/reload-skills` or new session.

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

## Tool Mapping Reference

Adapting skills from Claude Code ecosystem to Hermes:

| Claude Code | Hermes |
|-------------|--------|
| Read | read_file |
| Write | write_file |
| Edit | patch |
| Bash | terminal |
| Grep / Glob | search_files |
| Skill | skill_view |
| Task | delegate_task |
| TodoWrite | todo |
| WebSearch / WebFetch | ❌ Not available — remove or mark ⚠️ NOT_AVAILABLE |
| EnterPlanMode / ExitPlanMode | ❌ Not available — remove |

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
| `gh` CLI not installed | Source C unavailable | Sources A+B sufficient |
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

## Common Mistakes

### 1. API Quota & Format
SkillsMP: 50 req/day anonymous. API response is `{"success":true,"data":{"skills":[...]}}` (note: `data.skills`, not a direct array). Field is `author`, not `creator`.

### 2. Two Pre-Recommendation Checks
**Overlap check** — compare against Hermes built-in capabilities: memory/Hindsight/curator/brainstorming/writing-skills/systematic-debugging each cover "memory"/"learning"/"skill management"/"planning"/"skill writing"/"debugging" domains. Only recommend skills that fill clear gaps.

**Over-engineering check** — does this skill require isolation environments / evaluation agents / multi-round iteration? If yes → likely over-engineered. Personal use prioritizes lightweight, passively triggered, zero-maintenance skills.

### 3. Forgot to Check Existing Skills
Always run `skills_list` before recommending. Avoid recommending already-installed or functionally identical skills.

## Self-Test

After installation, verify it works:

```bash
hermes skills list | grep skill-finder   # confirm installed
# In a new session, say:
recommend               # should trigger 4-signal dynamic recommendation
is this safe? + URL     # should trigger quick security review
```

Not working? Run `/reload-skills` or start a new session.

## Red Lines

- Never auto-install — always require user confirmation
- Never skip security review
- Never modify skill core logic — only adapt tool names and paths
- 🔴 High-risk findings must be explicitly warned
- Mark uncertainties with ⚠️, never guess
