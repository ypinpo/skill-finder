import sys

# Read the file directly
with open(r"C:\Users\PP\AppData\Local\hermes\skills\skill-finder\SKILL.md", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Fix duplicate line
text = text.replace(
    "追问到能形成精准搜索关键词为止，然后进入 Step 1。\n\n追问 1-2 轮后，带着明确的 `q` 关键词进入 Step 1。",
    "追问到能形成精准搜索关键词为止，然后进入 Step 1。"
)

# 2. Replace personal cache path
text = text.replace(
    r"D:\AI\aios\Marvis\skills\market\skill-finder\.cache\<md5>.json",
    r"<hermes_home>/skills/skill-finder/.cache/<md5>.json"
)

# 3. Replace references/setup.md reference
text = text.replace(
    "见 `references/setup.md` — 可选 cron job 配置。",
    "可创建 cron job 每周自动同步 awesome 列表（详见下方「运维配置」）。"
)

# 4. Add tool-mapping inline
tool_mapping = """

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
"""
text = text.replace("\n## 常见问题", tool_mapping + "\n## 常见问题")

# 5. Add optional setup section before 工具映射
setup = """## 运维配置（可选）

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

"""
text = text.replace("\n## 工具映射参考", setup + "\n## 工具映射参考")

# Write release version
with open(r"D:\AI\Workspace\Hermes\default-profile\skill-finder-release.md", "w", encoding="utf-8") as f:
    f.write(text)

print(f"Lines: {text.count(chr(10))}, Chars: {len(text)}")
print("Done.")
