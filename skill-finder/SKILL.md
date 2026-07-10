---
name: skill-finder
description: "[EN] Multi-source skill discovery engine for Hermes Agent — search 2M+ skills across SkillsMP, GitHub, Gitee, ClawHub. Safety review + Hermes adaptation + one-click install. [CN] Use when the user asks about skills. Triggers: 有什么好用的skill/技能, 推荐skill/技能, 推荐几个skill/技能, 快推, 哪些skill/技能值得装, 找个skill/技能, 装个skill/技能, 发现skill/技能, 探索skill/技能. Do NOT trigger on: 列出skill/技能, 已装skill/技能, 我有什么skill/技能."
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

发现、审查、适配、安装第三方 skill 到 Hermes。

**启动时必须在首行输出横幅：**
> 🔍 *Skill Finder 已激活 — 多源聚合搜索 (SkillsMP + GitHub + Gitee + ClawHub) · 215万+ 技能索引*

## 概述

当前 Hermes 内置 `hermes skills search` 数据源太小，find-skills（Vercel）只做关键词匹配。本 skill 用 SkillsMP REST API（215 万+ 索引）+ LLM 审查来实现智能筛选。

**核心流程：澄清需求 → 搜索 → 候选展示 → 用户选择 → LLM 审查+改造 → diff 审核 → 安装。**
## 版权声明

本 Skill 的编排逻辑、审查模板及适配代码采用 MIT 协议开源。
引用的第三方 Skill 索引、API 数据及工具名称版权归原作者/平台所有。
Awesome 列表内容版权归原作者所有，本项目仅作聚合发现用途。

## 快速开始

说一句话就能用：

| 你说 | 效果 |
|------|------|
| 「推荐」 | 基于你的场景，精准推 3-4 个 skill |
| 「帮我找 XX 的 skill」 | 多源聚合搜索 |
| 「探索」 | 跨领域发现热门 skill |
| 「https://...SKILL.md 安全吗」 | 快速安全审查 |
| 「把这个 SKILL.md 装到 Hermes」 | 完整审查 → 适配改造 → 安装 |

## 使用示例

### 精准推荐
```
用户：推荐
Skill Finder：📌 上下文: Agent 运维 → otel-observability
             理由：补 Agent 可观测性空白，与现有监控互补
             🔍 缺口: PPT 生成 → ppt-generation
             理由：精选清单有但未装，字节出品 76k⭐
```
### 搜索安装
```
用户：帮我找个代码审查的 skill
Skill Finder：🔍 找到 8 个结果...
用户：装第 3 个
Skill Finder：🟢 安全 | 质量 8/10 | 改造 diff → 确认 → ✅ 已安装
```
### 快速审查
```
用户：https://github.com/xxx/SKILL.md 安全吗
Skill Finder：🟢 安全 — 无 shell 命令、无网络调用、无凭据操作
```

触发此 skill 后，先判断场景类型：

| 用户说 | 场景 | 处理方式 |
|--------|------|----------|
| "推荐skill" / "有什么好用的skill" / 无具体需求 | 主动推荐 | 跳到 Step 0-A |
| "推荐"/"快推技能"/"来几个技能" | 精准推荐技能 | 跳到 Step 0-A 精准模式 |
| "探索"/"有什么新鲜的skill"/"来点不一样的skill" | 探索发现 | 跳到 Step 0-A 探索模式 |
| "帮我找XX的skill" / "有没有XXskill" | 模糊搜索 | 跳到 Step 0-B |
| "https://github.com/xxx/SKILL.md 审查一下" | URL 审查 | 跳到 Step 3 |
| "这个skill安全吗" / "快查一下skill" + URL | 快速审查 | 跳到 Step 4-Quick |
| "帮我找个代码审查的skill"（具体明确） | 精准搜索 | 跳到 Step 1 |

### Step 0-A: 主动推荐（用户无明确需求）

当用户说"推荐skill""有什么好用的skill"，不要直接搜索。基于用户的已知信息推荐：

**推荐来源（多信号动态推断，不硬编码）：**

**首选：awesome 精选列表** — 社区人工维护的高质量 skill 集合，天然过滤垃圾：

| 仓库 | ⭐ | 覆盖领域 |
|------|-----|------|
| `obra/superpowers` | 248k | 通用开发工具 |
| `anthropics/skills` | 159k | Claude 官方技能 |
| `Shubhamsaboo/awesome-llm-apps` | 116k | LLM 应用/Agent |
| `vercel-labs/agent-skills` | 28k | Vercel AI 生态 |
| `kodustech/awesome-agent-skills` | 87 | Agent 技能精选 |
| `gmh5225/awesome-skills` | 41 | Agent 工具与资源 |

推荐时优先查这些列表中的 skill（已验证质量）。cron 每周自动同步新增条目（详见下方「运维配置」）。

**其次：4 信号动态推断** — 见上方「精准推荐」章节。每次推荐前实时运行，信号不足的方向静默跳过。

3. **精选清单** — 以下 skill 经过验证，直接推荐（跳过搜索）：

   | 推荐 skill | 适用场景 | 来源 |
   |-----------|----------|------|
   | `brainstorming` | 任何创作/开发前 | obra/superpowers（已验证） |
   | `code-reviewer` | 代码审查 | Shubhamsaboo/awesome-llm-apps |
   | `frontend-design` | 前端/UI 设计 | anthropics/skills |
   | `ppt-generation` | PPT 生成 | bytedance/deer-flow |
   | `docx` | Word 文档 | anthropics/skills |
   | `skill-creator` | 创建新 skill | anthropics/skills |
   | `ui-ux-pro-max` | 专业 UI/UX 设计 | nextlevelbuilder |
   | `browser-use` | 浏览器自动化 | browser-use |

4. **趋势推荐** — 用 SkillsMP API 查 `sortBy=stars` 的高星 skill

**输出格式**：基于 memory 动态生成 3 个方向选项再针对性推荐。不要使用硬编码的场景分类。

## 精准推荐：动态场景推断

**不再硬编码方向。** 从 4 个信号源动态推断 3-4 个方向，每个标注来源和置信度。

### 信号源（优先级排序）

| # | 信号 | 提取方式 | 标签 | 示例方向 |
|---|------|----------|------|----------|
| 1 | **当前上下文** | 对话中正在做的事 | `📌 上下文` | "在管理 cron → 推荐运维监控" |
| 2 | **能力缺口** | 精选清单 vs 已安装 skill | `🔍 缺口` | "精选清单有 ppt-generation，你未装" |
| 3 | **长期偏好** | `memory` 工具提取 | `🧠 偏好` | "长期关注 Agent 工具 → 推荐新 MCP skill" |
| 4 | **降级信号 (L1)** | 检查重叠/从未使用的 skill | `⚡ 降级` | "有 3 个代码审查 skill，可能只需 1 个" |

### 推断流程

```
① skills_list → 已安装列表
② memory → 提取活跃领域
③ 上下文 → 当前对话主题
④ 精选清单 ∩ 已安装 → 找缺口
⑤ 已安装 skill 交叉对比 → 找重叠/未使用
⑥ 综合推断 3-4 个方向 → 每个配 1 个推荐
```

### 输出格式

```
📌 上下文: [方向] → [skill]
   理由：解决什么问题 + 与当前场景的关联 + 与已有 skill 的差异
🔍 缺口: [方向] → [skill]  
   理由：同上，≤ 30 字，不套模板
🧠 偏好: [方向] → [skill]
   理由：同上
⚡ 降级: [方向] → [skill]
   理由：同上
```

**理由三要素**：① 解决的具体问题 ② 与用户的关联 ③ 与已有 skill 的差异。信号不足的方向静默跳过。

**探索发现模式**：当用户说"探索"/"有什么新鲜的"/"来点不一样的"，不受用户历史限制：

```
查询 SkillsMP API: sortBy=stars, 不限 category
→ 过滤已安装的
→ 只保留近期更新的（60 天内）
→ 跨领域取 Top 5
→ 标注每个 skill 所属领域
→ 展示时强调："以下是你可能不知道但值得关注的 skill"
```

探索模式的目的：打破个性化推荐的"信息茧房"，让用户发现完全没接触过的 skill 类型。

探索模式输出格式：
```
🔭 探索发现 — 你可能不知道但值得关注的 skill：

| # | 名称 | ⭐ | 领域 | 为什么值得关注 |
|---|------|-----|------|--------------|
| 1 | xxx  | 15k | 🎨 设计 | 即使不做设计，思路可借鉴 |
```

### Step 0-B: 澄清提问（需求模糊时）

当用户只说"帮我找XX的skill"但没有说清用途时，**不要直接搜索**。先 `clarify` 追问：

用自然对话追问 1-2 轮，不要抛问卷。参考话术：

- "测试 skill 有很多种——你是写单元测试、做 E2E、还是压测？"
- "这个 skill 是想一次性解决，还是日常反复用？影响推荐方向"
- "你更看重可靠性（高 star 大厂出品）还是想尝鲜？"
- "你已经有 XX skill 了，需要的是补充还是替代？"

追问到能形成精准搜索关键词为止，然后进入 Step 1。

## 工作流

## 隐私声明

- **SkillsMP API**：搜索关键词会发送到 `skillsmp.com`（匿名，无账号关联）
- **web_search**：通过 Bing 搜索（`cn.bing.com`）
- **GitHub API**：仅在使用 `gh auth login` 后启用，否则跳过
- **本地缓存**：搜索结果缓存在 `<hermes_home>/skills/skill-finder/.cache/`，不上传
- **审查过程**：SKILL.md 原文仅在当前会话中分析，不持久化存储

### Step 1: 搜索（多源聚合）

**三源并行搜索，合并去重：**

**源 A — SkillsMP API（主力，实测 341ms）：**
```bash
curl -s "https://skillsmp.com/api/v1/skills/search?q=<QUERY>&sortBy=stars&limit=10"
```

**源 B — web_search 补充（覆盖中文生态 + 国内平台）：**
```
web_search "site:github.com SKILL.md <QUERY>"     → GitHub
web_search "site:gitee.com SKILL.md <QUERY>"       → Gitee 国内源
web_search "ClawHub skill <QUERY>"                 → 中文 skill 镜像
```

**源 C — GitHub API（结构化数据）：**
```bash
gh search repos "SKILL.md" --topic agent-skills --sort stars --limit 10
```

**合并策略：**
1. 三源并行发起
2. **先查缓存**：搜索前查 `<hermes_home>/skills/skill-finder/.cache/<md5>.json`，命中且 24h 内直接返回，跳过 API 调用
3. 未命中 → 执行 API 搜索 → 结果写入缓存（JSON 格式，含 `{timestamp, results}`）
4. **质量门控**：SkillsMP 返回后，统计 ⭐≥10 的高质量结果数。若 < 3 个 → 强制触发源 B+C 补搜
5. **去重键降级链**：
   - githubUrl 存在 → 用 githubUrl
   - githubUrl 缺失 → 用 `name + author` 联合去重
   - 两者都缺 → 保留但标注 ⚠️
6. 统一按 stars 降序排列

**合并示例逻辑：**
```python
# 伪代码
results = skillsmp_results + github_results
seen_repos = set()
merged = []
for r in sorted(results, key=lambda x: x['stars'], reverse=True):
    repo = extract_repo_path(r['url'])
    if repo not in seen_repos:
        seen_repos.add(repo)
        merged.append(r)
return merged[:10]
```

### Step 2: 展示候选

将搜索结果格式化为表格：

```
| # | 名称 | ⭐ | 热度 | 作者 | 描述 |
|---|-----|-----|------|------|
| 1 | xxx  | 12k | 🔥 | org/repo | 一句话描述... |
```

⭐ 热度标注规则（自动附加）：
- ⭐ ≥ 1,000 → 🔥 热门
- ⭐ 100-999 → 🟢 正常
- ⭐ 10-99 → 🟡 低热度，谨慎
- ⭐ < 10 → ⚠️ 几乎无人使用，建议跳过

使用 `clarify` 让用户选择。**不要自动选第一个**。⭐ < 10 的 skill 默认标注 ⚠️ 提醒用户。

### Step 3: 获取 SKILL.md

从 SkillsMP 返回的 `repo` 字段构造 GitHub raw URL：
- 格式：`https://raw.githubusercontent.com/<org>/<repo>/main/<path>/SKILL.md`
- 路径因仓库而异，常见的：`skills/<name>/SKILL.md` 或 `<name>/SKILL.md`

用 `curl -sL "<raw_url>"` 获取完整 SKILL.md 内容。

**备用方案**：如果 raw URL 不可用，用 GitHub API：
```bash
# Use GitHub API to fetch base64-encoded content, then decode locally
# curl https://api.github.com/repos/<org>/<repo>/contents/<path>/SKILL.md
```

GitHub API 无认证限频 60次/小时，认证后 5000次/小时。

### Step 4-Quick: 快速审查模式（仅安全检查）

当用户说"这个安全吗""快查一下"，只做安全审查，跳过质量评估和 Hermes 适配。

审查提示（简化版）：

```
你是 Agent Skill 安全审查专家。快速扫描以下 SKILL.md，重点检查：

| 维度 | 检查项 |
|------|--------|
| Shell 命令 | 文件删除, 管道执行, eval, 提权 |
| 网络行为 | 向外部域名 POST、下载二进制 |
| 文件访问 | 读取敏感配置, 写入系统路径 |
| 凭据操作 | 读取/发送 API key、token |
| 依赖安装 | pip/npm/apt 安装未知包 |

输出：🟢 安全 / 🟡 需注意（列出具体风险）/ 🔴 危险（阻止安装）
```

快速模式只输出风险评级 + 风险清单。不做改造，不输出完整 SKILL.md。

### Step 4: LLM 审查 + 改造（完整模式）

用一份 LLM 调用同时完成三件事。审查提示模板：

```
你是 Agent Skill 安全审查专家。分析以下 SKILL.md，输出结构化报告。

## 安全审查（六维度）

对每个维度打分：🟢安全 / 🟡需注意 / 🔴危险

| 维度 | 风险 | 发现 |
|------|------|------|
| Shell 命令 | ? | 列出所有 shell 命令，标注危险模式 |
| 网络行为 | ? | 列出所有网络调用，检查域名 |
| 文件访问 | ? | 列出文件操作路径，检查越权 |
| 凭据操作 | ? | 是否读取/使用 API key、token |
| 依赖安装 | ? | pip/npm/apt 等安装命令 |
| 提权/逃逸 | ? | 提权、容器逃逸、权限变更 等 |

## 质量评估

- SKILL.md 完整度（frontmatter / 触发条件 / 步骤 / 示例）：X/10
- 适用性：是否解决实际问题
- 维护状态：仓库活跃度

## Hermes 适配

对照下方「工具映射参考」改造 SKILL.md：

改造原则：
1. 只改 tool 名映射 + 路径适配 + 平台标记
2. 不在 Hermes 中存在的工具（WebSearch/WebFetch/EnterPlanMode），移除对应步骤或标注 ⚠️ NOT_AVAILABLE
3. 路径中的 POSIX 假设标注 ⚠️ WINDOWS_CHECK
4. 在 frontmatter 添加 adapted_for: hermes, adapted_from: <原始URL>
5. 所有改动用 <!-- ADAPTED: reason --> 注释标注
6. 不确定的地方标 ⚠️ NEEDS_REVIEW 而非猜测

输出格式：
---
## 审查报告
[安全审查表格 + 质量评分 + 关键发现]

## 改造后的 SKILL.md
[完整改造内容]
---
```

### Step 5: 展示 diff + 审查报告

用 `patch` 工具展示改造前后的 diff。同时展示审查报告。

**让你审核后再安装。你拥有最终决定权。**

如果审查发现 🔴 高危项，必须明确警告并等你确认。

### Step 6: 安装

你确认后，用 `write_file` 将改造后的 SKILL.md 写入：
```
~/.hermes/skills/<skill-name>/SKILL.md
```

改造后的 skill 在下次 `/reload-skills` 或新会话中生效。

## 分类筛选速查

用户可能按领域搜索，可用 category 参数精炼：

| 领域 | category slug |
|------|---------------|
| 开发 | development |
| 测试与安全 | testing-security |
| 数据与 AI | data-ai |
| DevOps | devops |
| 文档 | documentation |
| 内容与媒体 | content-media |
| 工具 | tools |
| 商业 | business |

## 扩展数据源

当前主力源是 SkillsMP API。未来可扩展：

- **GitHub 直搜**：`gh search code "SKILL.md" --filename-match --sort stars`
- **ClawHub 中文镜像**：`cn.clawhub-mirror.com`（无 API，需手动浏览）
- **腾讯 SkillHub**：`skillhub.tencent.com`（无 API，手动提交 URL）
- **国内厂商平台**：暂无公开 API，当有 URL 时可手动加入审查队列

遇到用户提供了具体 skill URL（GitHub raw / Gitee / 其他），跳过 Step 1-2，直接从 Step 3 开始。

## 精选清单自动更新

可创建 cron job 每周自动同步 awesome 列表（详见下方「运维配置」）。

## 运维配置（可选）

可创建 cron job 每周自动同步 awesome 列表中的新 skill：

```
cronjob create
  name: skill-finder-curated-refresh
  schedule: "30 10 * * 0"
  prompt: |
    阶段1 — SkillsMP API: sortBy=stars, limit=20
    阶段2 — awesome 列表抓取:
      github.com/obra/superpowers
      github.com/anthropics/skills
      github.com/Shubhamsaboo/awesome-llm-apps
      github.com/vercel-labs/agent-skills
      github.com/kodustech/awesome-agent-skills
      github.com/gmh5225/awesome-skills
    阶段3 — 去重合并 → 过滤已安装 → star>500 → ≤15个
  enabled_toolsets: [terminal, file]
```

先执行 `gh auth login`。


## 工具映射参考

从 Claude Code 生态适配 skill 到 Hermes：

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
| WebSearch / WebFetch | ❌ 不存在，移除或标注 ⚠️ NOT_AVAILABLE |
| EnterPlanMode / ExitPlanMode | ❌ 不存在，移除 |

## 已知限制

| 限制 | 影响 | 缓解 |
|------|------|------|
| SkillsMP 匿名 50次/天 | 频繁搜索触发配额 | 24h 缓存 + GitHub 备用源 |
| GitHub raw 可能超时 | SKILL.md 获取失败 | GitHub API 备用 |
| `gh` CLI 未安装 | 源 C 不可用 | 源 A+B 足够 |
| 跨领域 skill 质量低 | 探索模式结果稀疏 | 主要依赖 awesome 列表 |
| 审查靠 LLM 内联 | 复杂 skill 可能漏检 | diff 审核作为人工闸门 |


## 常见问题

### SKILL.md 无法获取

某些仓库路径不标准。尝试：
1. 仓库根目录 `SKILL.md`
2. `skills/<name>/SKILL.md`
3. 用 GitHub API 列出仓库内容找

### Windows: python -c 多行被截断

Windows git-bash 下 `python -c "..."` 含多行会被 cmd 截断（报 `IndentationError` 或 `goto :error`）。**必须用 `write_file` 写脚本文件，再 `terminal("python script.py")` 执行。**

### 改造后不可用

如果改造后的 skill 运行出错：
1. 先用原始 SKILL.md 测试是否是改造引入的问题
2. 如果是，回退到只做 tool 映射的最小改造
3. 必要时手动调试

## 常见错误

### 1. API 配额与格式

SkillsMP 匿名 50次/天。超限时告知用户，建议注册获取 API Key（500次/天），或等次日重置。API 返回结构为 `{"success":true,"data":{"skills":[...]}}`（注意 `data.skills` 不是直接数组），字段 `author` 不是 `creator`。

### 2. 推荐前两大检查

**功能重叠** — 对照 Hermes 已有能力：memory/Hindsight/curator/brainstorming/writing-skills/systematic-debugging 各自覆盖了"记忆""学习""skill管理""规划""写skill""调试"类。只有填补明确空白才推荐。

**过度工程化** — skill 是否需要隔离环境/评估 Agent/多轮迭代？如果是 → 大概率过度。个人场景优先轻量、被动触发、零维护。

### 3. 忘记查重

推荐前必须 `skills_list` 查看已有 skill。

## 自检

安装后验证生效：

```bash
hermes skills list | grep skill-finder   # 确认已装
# 新会话中说：
推荐                    # 应触发 4 信号动态推荐
这个安全吗 + GitHub URL  # 应触发快速审查
```

未生效？执行 `/reload-skills` 或开启新会话。


## 红线

- 不要自动安装，必须用户确认
- 不要跳过安全审查
- 不要改 skill 的核心逻辑，只做适配
- 遇到 🔴 高危必须明确警告
- 不确定的地方标 ⚠️，不猜测
