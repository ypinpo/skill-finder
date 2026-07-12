---
name: skill-finder
description: "[EN] Multi-source skill discovery engine for Hermes Agent — search 2M+ skills across SkillsMP, GitHub, Gitee, and ClawHub. Safety review + cross-agent adaptation + one-click install. Triggers EN: recommend skill/skills, find skill, install skill, discover skill, explore skill. Triggers CN: 有什么好用的skill/技能, 推荐skill/技能, 快推, 哪些skill/技能值得装, 找个skill/技能, 装个skill/技能, 发现skill/技能, 探索skill/技能."
version: 1.10.0
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
| "有什么好用的skill" / no specific request | Active recommendation | Go to Step 0-A |
| "recommend" / "快推skill" / "来几个skill" | Precise recommendation | Go to Step 0-B |
| "explore" / "探索skill" / "有什么新鲜的skill" | Exploration discovery | Go to Step 0-C |
| "find me a skill for X" / "有没有XXskill" | Fuzzy search | Go to Step 0-D (clarify) |
| Direct URL to SKILL.md | URL review | Go to Step 3 |
| "is this safe?" + URL | Quick review | Go to Step 4-Quick |

## Step 0-A: Active Recommendation (无明确需求)

直接基于精选清单推荐高质量技能，目标 3-4 个。

### 推荐源（Primary: Awesome Curated Lists）

| Repository | ⭐ | Domain |
|-----------|-----|--------|
| `obra/superpowers` | 248k | General dev tools |
| `anthropics/skills` | 159k | Official Claude skills |
| `Shubhamsaboo/awesome-llm-apps` | 116k | LLM apps / agents |
| `vercel-labs/agent-skills` | 28k | Vercel AI ecosystem |
| `heilcheng/awesome-agent-skills` | 6k | Agent skill aggregation 🆕 |
| `codesstar/hermes-skill-atlas` | — | Hermes 专用 70+ skill 浏览器 🆕 |
| `kodustech/awesome-agent-skills` | 87 | Agent skill curation |
| `gmh5225/awesome-skills` | 41 | Agent tools & resources |

**提取方法**：对每个仓库，使用 `web_search` 获取 README 内容，解析 Markdown 链接提取技能名称与 GitHub URL（优先完整 repo 链接，其次相对路径补全）。**Hermes 专用优先**：`codesstar/hermes-skill-atlas` 提供 70+ 个已验证的 Hermes skill，优先查询此源。技能列表本地缓存至 `<skills_dir>/skill-finder/.cache/curated.json`，每周刷新（见 Operations Setup）。

展示时按 domain 分组，标注来源和 ⭐，过滤掉已安装 skill（通过 `skills_list` 获取已安装名称，并排除完全匹配项）。

## Step 0-B: Precise Recommendation (有偏好但非明确搜索词)

基于 4 信号动态推断 3-4 个方向，每个方向配 1 个推荐。

| # | 信号 | 来源 | 标签 | 示例 |
|---|--------|--------|-------|---------|
| 1 | 当前上下文 | 正在处理的任务 | `📌 Context` | "管理 cron → 推荐 ops 监控" |
| 2 | 能力缺口 | 精选列表 vs 已安装 | `🔍 Gap` | "精选列表有 ppt-gen，未安装" |
| 3 | 长期偏好 | `memory` 工具提取的偏好 | `🧠 Preference` | "偏好 Agent 工具 → 推荐新 MCP skill" |
| 4 | 降级 (L1) | 重叠/从未使用的 skill | `⚡ Degrade` | "3 个 code review skill，可保留 1 个" |

### 推断流程
1. 获取已安装 skill 列表（通过内置 `skills_list` 或文件系统扫描）。
2. 读取持久偏好/记忆 → 活跃领域。
3. 当前上下文 → 会话主题。
4. 精选列表 ∩ 已安装 → 找出缺口。
5. 交叉对比已安装 → 发现重叠/零使用。
6. 综合 3-4 方向，每个方向推荐 1 个 skill，确保不推荐已安装项。

### 输出格式
📌 Context: [方向] → [skill]
理由: 解决的问题 + 相关性 + 与已安装的区别
🔍 Gap: [方向] → [skill]
理由: (同上，30 词以内)
🧠 Preference: [方向] → [skill]
⚡ Degrade: [方向] → [skill]

text
信号弱的方向静默跳过。

## Step 0-C: Exploration Discovery (发现新鲜skill)

无历史约束，纯粹基于 SkillsMP API 最新趋势。

**方法**：调用 SkillsMP API `sortBy=stars`，过滤 `updatedAt` 在 60 天内，跨领域取前 5 展示。展示前过滤已安装 skill。格式同 Step 2。

## Step 0-D: Clarifying Questions (模糊搜索前)

当用户请求模糊时，问 1-2 个自然追问：
- "Testing skills 有很多种——单元测试、E2E 还是压力测试？"
- "是一次性任务还是每天都要用？这影响我推荐的方向。"
- "偏好久经考验（高星知名）还是前沿新秀？"

继续追问直到形成精确搜索词，然后进入 Step 1。

## Step 1: Search (分层搜索)

按质量从高到低分层，上层命中 ≥5 个候选即停止。

### L0 — 精选清单 + awesome 列表（质量 🟢）
使用 Step 0-A 中缓存的精选技能列表（`curated.json`），按关键词模糊匹配（名称、描述、标签）。若缓存不存在或过期（>7天），实时拉取并解析。
**L0 终止条件**：命中 ≥ 5 个候选 → 跳到 Step 2。

### L1 — SkillsMP API 主力 + GitHub/Gitee 并行（质量 🟡/🟢）
L0 不足 5 个时发起。

**SkillsMP API（主力，~300ms）：**
```bash
curl -s "https://skillsmp.com/api/v1/skills/search?q=<QUERY>&sortBy=stars&limit=10"
```
响应结构：`{"success":true,"data":{"skills":[...]}}`，结果在 `data.skills`，字段名 `author`（非 `creator`），`stars`，`updatedAt` 等。

**GitHub/Gitee 补充（web_search）：**

text
web_search "site:github.com/topics agent-skill <QUERY>"
web_search "site:github.com SKILL.md <QUERY> agent language:Markdown"
web_search "site:gitee.com <QUERY> skill SKILL.md"
解析搜索结果 URL，提取 `github.com/<org>/<repo>`。

**L1 终止条件**：命中 ≥ 5 个候选 → 跳到 Step 2。

### L2 — GitHub API 深度搜索（可选，需 `gh auth login`）
L0+L1 仍不足 5 个时：

```bash
gh search repos "SKILL.md" --topic agent-skills --sort stars --limit 10
```

### 合并与去重

1. **24h 缓存优先**：检查 `<skills_dir>/skill-finder/.cache/<md5>.json`，命中且 < 24h 直接返回。
2. 缓存未命中 → 按 L0→L1→L2 层级执行 → 写入缓存。
3. 去重键：`githubUrl` 优先；无则用 `name + author` 联合键。
4. **排除已安装 skill**：获取已安装 skill 列表（`skills_list`），去除名称完全匹配的项。
5. 合并后按综合评分（Step 2）排序。

若最终可用结果 <3，明确告知用户"搜索结果较少，建议放宽关键词"，不强行凑数。

## Step 2: Composite Scoring + Display

统一数据模型：无论来源，每个候选项标准化为：

```json
{
  "name": "skill-name",
  "author": "author",
  "githubUrl": "https://github.com/org/repo",
  "stars": 1200,
  "updatedAt": "2025-06-01T...",
  "source": "awesome|skillsmp|github_topic|github_file|gitee",
  "description": "...",
  "path": "SKILL.md 路径 (如 root 或 skills/name/SKILL.md)"
}
```

综合评分公式：

```
score = stars_norm × 0.4 + freshness × 0.3 + activity × 0.2 + source_quality × 0.1

stars_norm = min(stars / 1000, 1.0)
freshness = max(0, 1 - (today - updatedAt_days) / 365)
activity = max(0, 1 - (today - last_commit_days) / 365)   # 若无法获取 last_commit_days，使用 freshness 替代
source_quality = awesome×1.0 | skillsmp×0.8 | github_topic×0.7 | github_file×0.6 | gitee×0.5
```

热度标注：

| 标注 | 条件 |
|------|------|
| 🔥 热门 | score ≥ 0.7 |
| 🟢 正常 | 0.3 ≤ score < 0.7 |
| 🟡 谨慎 | 0.1 ≤ score < 0.3 |
| ⚠️ 跳过 | score < 0.1（不展示） |

展示格式：

```
| # | 名称 | 综合分 | ⭐ | 热度 | 来源 | 描述 |
|---|-----|--------|-----|------|------|------|
| 1 | xxx  | 0.85   | 12k | 🔥  | SkillsMP | 一句话描述... |
```

使用编号让用户选择（`clarify` 等待输入），禁止自动选第一个。

## Step 3: Fetch SKILL.md

根据用户选择的候选项，获取 SKILL.md 原文。

**路径推断优先级**：

1. 搜索结果中若已包含 `path` 字段，直接使用。
2. 若为 GitHub 仓库，尝试以下路径顺序：
   - 仓库根目录 `SKILL.md`
   - `skills/<name>/SKILL.md`
   - 调用 GitHub API `GET /repos/<org>/<repo>/contents/` 列出根目录，搜索包含 SKILL.md 的条目。
3. 若失败，提示用户手动提供路径。

**获取方法**：

主方案：GitHub API
```bash
curl -s -H "Accept: application/vnd.github.v3+json" "https://api.github.com/repos/<org>/<repo>/contents/<path>/SKILL.md"
```
从响应的 `content` 字段 Base64 解码得到原文。若需要认证，先检查 `gh auth status`，未登录则退回到 raw URL。

备用方案：raw URL
```
https://raw.githubusercontent.com/<org>/<repo>/main/<path>/SKILL.md
```

**24h 缓存**：获取成功后写入 `<skills_dir>/skill-finder/.cache/<org>_<repo>.md`，下次同一仓库 24h 内直接读缓存。

**限流处理**：GitHub API 匿名 60 次/小时，认证 5000 次/小时。遇 403/429 时提示用户执行 `gh auth login` 或稍后再试。

## Step 4-Quick: Fast Security Review

当用户仅问 "这个安全吗？"+ URL 时，执行安全专用审查：

| 维度 | 检查点 |
|------|--------|
| Shell 命令 | 文件删除、管道执行、eval、权限提升 |
| 网络 | 向未知域名 POST、二进制下载 |
| 文件访问 | 读取敏感配置（.env、~/.ssh），写入系统路径 |
| 凭证 | 读取/发送 API key、token |
| 依赖 | pip/npm/apt 安装未知包 |

输出：🟢 Safe / 🟡 Caution（列出风险点）/ 🔴 Dangerous（阻止安装）。

## Step 4: LLM Review + Adaptation (Full Mode)

单个 LLM 调用同时完成三项任务：

**安全审查（6 维度）**
每项评分 🟢/🟡/🔴：Shell 命令、网络、文件访问、凭证、依赖、权限提升。

**质量评估**
- SKILL.md 完整性（frontmatter / triggers / steps / examples）：X/10
- 实用性：是否解决真实问题？
- 维护性：仓库近期活动（最近 commit、Issue 响应）

**跨代理适配**
基于 Tool Mapping Reference（见下文）进行工具名/路径/平台标记映射。原则：
1. 仅映射工具名 + 路径 + 平台标记。
2. 当前代理不可用的工具（如 WebSearch、WebFetch、EnterPlanMode）移除对应步骤，并标注 ⚠️ NOT_AVAILABLE。
3. POSIX 假设处标注 ⚠️ WINDOWS_CHECK（如 `#!/bin/bash`）。
4. 在 frontmatter 添加 `adapted_for: <agent_name>, adapted_from: <original URL>`。
5. 所有改动注释 `<!-- ADAPTED: reason -->`。
6. 不确定的映射标注 ⚠️ NEEDS_REVIEW，严禁猜测。

适配输出：完整的、可直接安装的 SKILL.md 内容（适配后版本）。

## Step 5-6: Diff Review + Install

1. 将适配后的内容写入临时文件 `adapted_skill.md`。
2. 与原始文件（从缓存 `<org>_<repo>.md` 读取）使用 `diff -u original_skill.md adapted_skill.md` 生成差异。
3. 向用户展示差异，等待确认。
4. 用户确认后，将适配后的 skill 写入代理技能目录（如 `~/.hermes/skills/<skill-name>.md`）。
5. 提示用户执行 `[reload skills]` 或开启新会话使其生效。
6. 记录反思日志（见自增强接口）。

## Multi-Agent Tool Mapping Reference

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

WebSearch/WebFetch/EnterPlanMode 等工具并非所有代理均支持，审查时按上表移除或标记为 NOT_AVAILABLE。

## Category Filter Reference

SkillsMP 分类 slug 参考：

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

## 过度工程化检查（推荐前必执行）

推荐任何 skill 前，判断其是否过度设计，命中任一信号即跳过：

| 信号 | 判断标准 | 处理 |
|------|----------|------|
| 隔离环境 | 需要 Docker/VM/独立沙箱执行 | 跳过 — 个人使用场景不需要隔离 |
| 评估代理 | 内部启动子 Agent 做多轮评估 | 跳过 — 单次 LLM 审查即够 |
| 持久化服务 | 需要常驻进程/数据库/消息队列 | 跳过 — 优先零依赖的轻量 skill |
| 多轮迭代 | 需要训练/RLHF/自进化循环 | 跳过 — 个人微调收益不成比例 |

**原则**：个人使用优先轻量、被动触发、零维护的 skill。

## Common Mistakes

1. **SkillsMP API 响应陷阱**：数据在 `data.skills`，不是直接数组，字段名 `author` 非 `creator`。
2. **推荐前双重检查**：① 查重（对照已安装 skill + 内置能力）；② 过度工程化检查。二者缺一不可。
3. **搜索结果不足时降级**：L0 < 5 → L1；L0+L1 < 5 且 L2 不可达 → 明确提示用户放宽关键词，不硬凑。
4. **适配时猜测映射**：不确定的映射必须标 ⚠️ NEEDS_REVIEW，当前 Agent 无等价工具时直接标注 NOT_AVAILABLE 并移除步骤。

## Red Lines

- 绝不自动安装 — 始终需用户确认
- 绝不跳过安全审查
- 绝不修改 skill 核心逻辑 — 仅适配工具名和路径
- 🔴 高风险发现必须明确警告
- 不确定的标注 ⚠️，绝不猜测

## 自增强接口（反思日志）

<!-- reflections:auto-start -->
<!-- 每次搜索/推荐完成后，在下方追加一行反思：
     [YYYY-MM-DD] SEARCH: q=关键词, results=N, score_range=X-Y, user_action=选择/拒绝/追问
     [YYYY-MM-DD] RECOMMEND: scene=场景, accepted=是/否, reason=用户反馈
     同类信号累积 3 次 → 触发场景/策略自更新
-->
<!-- reflections:auto-end -->

执行时请将日志写入 `<skills_dir>/skill-finder/.cache/reflections.log`。

## Operations Setup (Optional)

创建 cron job 每周同步精选列表（也用于 L0 缓存更新）：

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
      github.com/heilcheng/awesome-agent-skills
      github.com/codesstar/hermes-skill-atlas
      github.com/kodustech/awesome-agent-skills
      github.com/gmh5225/awesome-skills
    Phase 3 — Dedup & merge: filter installed → exclude existing → star>500 → ≤15 items
  enabled_toolsets: [terminal, file]
```

需先执行 `gh auth login`。

## Privacy Notice

- **SkillsMP API**：搜索关键词发送至 `skillsmp.com`（匿名，无账号关联）
- **web_search**：通过 Bing（`cn.bing.com`）
- **GitHub API**：仅在 `gh auth login` 后启用，否则跳过
- **本地缓存**：结果缓存在 `<hermes_home>/skills/skill-finder/.cache/`，绝不上传
- **审查过程**：SKILL.md 内容仅在当前会话分析，不持久存储

## Known Limitations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| SkillsMP 匿名 50 req/day | 频繁搜索触及配额 | 24h 缓存 + GitHub 回退 |
| GitHub raw 可能超时 | SKILL.md 获取失败 | GitHub API 回退 |
| `gh` CLI 未安装 | L2 不可用 | L0+L1 通常足够 |
| 跨领域 skill 质量低 | 探索结果稀疏 | 主要依赖精选列表 |
| LLM inline review 可能漏报 | 复杂 skill 有误判风险 | diff review 作为人工防线 |

## Troubleshooting

### SKILL.md Not Found
尝试路径：仓库根目录 `SKILL.md` → `skills/<name>/SKILL.md` → GitHub API 列出根目录查找。若均失败，请求用户提供准确路径。

### Windows: python -c 多行截断
Windows git-bash 会截断多行 `python -c "..."`（导致 `IndentationError`），必须用 `write_file` 创建脚本文件再用 `terminal("python script.py")` 执行。
