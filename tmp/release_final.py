with open(r"D:\AI\Workspace\Hermes\default-profile\skill-finder-release.md", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Quick start / TL;DR - insert after overview (after the core flow line)
quickstart = """
## 快速开始

说一句话就能用：

| 你说 | 效果 |
|------|------|
| 「推荐」 | 基于你的场景，精准推 3-4 个 skill |
| 「帮我找 XX 的 skill」 | 多源聚合搜索 |
| 「探索」 | 跨领域发现热门 skill |
| 「https://...SKILL.md 安全吗」 | 快速安全审查 |
| 「把这个 SKILL.md 装到 Hermes」 | 完整审查 → 适配改造 → 安装 |

"""

old1 = "**核心流程：澄清需求 → 搜索 → 候选展示 → 用户选择 → LLM 审查+改造 → diff 审核 → 安装。**"
text = text.replace(old1, old1 + quickstart)

# 2. Usage examples - insert after quick start
examples = """## 使用示例

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

"""

text = text.replace(quickstart, quickstart + examples)

# 3. Privacy notice - insert before "## Step 1: 搜索"
privacy = """## 隐私声明

- **SkillsMP API**：搜索关键词会发送到 `skillsmp.com`（匿名，无账号关联）
- **web_search**：通过 Bing 搜索（`cn.bing.com`）
- **GitHub API**：仅在使用 `gh auth login` 后启用，否则跳过
- **本地缓存**：搜索结果缓存在 `<hermes_home>/skills/skill-finder/.cache/`，不上传
- **审查过程**：SKILL.md 原文仅在当前会话中分析，不持久化存储

"""

text = text.replace("\n### Step 1: 搜索（多源聚合）", privacy + "### Step 1: 搜索（多源聚合）")

# 4. Known limitations - insert before "## 常见问题"
limits = """## 已知限制

| 限制 | 影响 | 缓解 |
|------|------|------|
| SkillsMP 匿名 50次/天 | 频繁搜索触发配额 | 24h 缓存 + GitHub 备用源 |
| GitHub raw 可能超时 | SKILL.md 获取失败 | GitHub API 备用 |
| `gh` CLI 未安装 | 源 C 不可用 | 源 A+B 足够 |
| 跨领域 skill 质量低 | 探索模式结果稀疏 | 主要依赖 awesome 列表 |
| 审查靠 LLM 内联 | 复杂 skill 可能漏检 | diff 审核作为人工闸门 |

"""

text = text.replace("\n## 常见问题", limits + "\n## 常见问题")

# 5. Self-test - insert before "## 红线"
selftest = """## 自检

安装后验证生效：

```bash
hermes skills list | grep skill-finder   # 确认已装
# 新会话中说：
推荐                    # 应触发 4 信号动态推荐
这个安全吗 + GitHub URL  # 应触发快速审查
```

未生效？执行 `/reload-skills` 或开启新会话。

"""

text = text.replace("\n## 红线", selftest + "\n## 红线")

with open(r"D:\AI\Workspace\Hermes\default-profile\skill-finder-release.md", "w", encoding="utf-8") as f:
    f.write(text)

print(f"Lines: {text.count(chr(10))}, Chars: {len(text)}")
