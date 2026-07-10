# Skill Finder 运维配置（参考）

可选，不属于核心工作流。

## 精选清单自动更新（cron）

可创建 cron job 每周刷新精选清单：

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
    阶段3 — 去重合并: 过滤已安装 → 排除已有 → star>500 → ≤15个
  enabled_toolsets: [terminal, file]
```

先执行 `gh auth login`（GitHub 搜索需要）。

## awesome 列表源

| 仓库 | ⭐ | 覆盖领域 |
|------|-----|------|
| `obra/superpowers` | 248k | 通用开发工具 |
| `anthropics/skills` | 159k | Claude 官方技能 |
| `Shubhamsaboo/awesome-llm-apps` | 116k | LLM 应用/Agent |
| `vercel-labs/agent-skills` | 28k | Vercel AI 生态 |
| `kodustech/awesome-agent-skills` | 87 | Agent 技能精选 |
| `gmh5225/awesome-skills` | 41 | Agent 工具与资源 |
