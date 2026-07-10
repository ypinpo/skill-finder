---
name: self-improving-agent
description: Use when the user corrects you, points out mistakes, or after completing significant work. Triggers on: user corrections ("错了", "应该是", "记住我"), preference signals ("我喜欢", "永远不要"), repeated instructions (3+ times), or self-reflection after multi-step tasks. Agent evaluates its own work, catches mistakes, and improves permanently through Hermes memory + Hindsight.
version: 2.0.0
author: Adapted from TeamWiseFlow/self-improving
license: MIT
metadata:
  hermes:
    tags: [self-improvement, learning, memory, reflection]
    related_skills: [brainstorming, writing-skills, agent-self-improvement]
    adapted_for: hermes
    adapted_from: https://github.com/TeamWiseFlow/xiaobei/tree/master/_disabled/skills/self-improving
---

# 自我改进 Agent（主动反思）

<!-- ADAPTED: 文件存储 → Hermes memory + Hindsight 双层记忆 -->
<!-- ADAPTED: clawdbot/clawhub → Hermes 原生工具 -->

在每次被纠正和每次完成任务后，主动反思并积累知识。不需要手动维护。

## 何时使用

- 用户纠正你或指出错误
- 完成重要任务后想要评估结果
- 你注意到自己的输出有改进空间
- 知识应该随时间积累，不需要人工维护

## 架构

⚠️ ADAPTED: 原文使用 `~/self-improving/` 文件系统，改为 Hermes 双层记忆：

```
记忆层级：
├── Hermes memory 工具     # HOT: 偏好 + 高频规则（≤2200 char 总预算）
├── Hindsight retain       # WARM: 项目经验、领域知识（语义检索）
└── session_search         # COLD: 历史会话中的具体上下文
```

| Tier | 存储位置 | 容量 | 行为 |
|------|----------|------|------|
| HOT | `memory(action='add')` | 2200 char | 每次会话注入 |
| WARM | `hindsight_retain()` | 不限 | 语义检索，按需加载 |
| COLD | `session_search()` | 不限 | 显式搜索历史会话 |

## 检测触发器

**纠正信号** → 存入 Hindsight + 评估是否升级到 memory：
- "不对，应该是……"
- "你错了"
- "记住，我永远……"
- "我之前告诉过你……"
- "别再……"
- "你为什么总是……"

**偏好信号** → 直接存入 Hermes memory：
- "我喜欢你……的时候"
- "永远帮我……"
- "绝对不要……"
- "我的风格是……"
- "对于 XX 项目，用……"

**模式候选** → Hindsight 记录，出现 3 次后升级到 memory：
- 同一指令重复 3 次以上
- 反复成功的工作流
- 用户称赞特定方式

**忽略**（不记录）：
- 一次性指令（"现在做 XX"）
- 上下文特定（"在这个文件里……"）
- 假设性问题（"如果……会怎样"）

## 自我反思

完成重要任务后，暂停评估：

1. **达到预期了吗？** — 结果 vs 意图
2. **哪里可以更好？** — 下次改进点
3. **这是模式吗？** — 如果是，存入 Hindsight

**何时反思：**
- 完成多步骤任务后
- 收到反馈后（正面或负面）
- 修复 bug 或错误后
- 注意到自己输出可以更好时

**日志格式（存入 Hindsight）：**
```
CONTEXT: [任务类型]
REFLECTION: [注意到的]
LESSON: [下次怎么做不同]
```

3 次成功应用的反思 → 升级到 Hermes memory。

## 快速查询

⚠️ ADAPTED: 原文查文件，改为查 Hermes 记忆系统

| 用户说 | 操作 |
|--------|------|
| "你了解我的什么？" | `memory` + `hindsight_recall("preferences")` |
| "你学到了什么？" | `hindsight_reflect("recent learnings")` |
| "我有什么模式？" | 读取 memory 条目 |
| "搜索 XX 相关记忆" | `hindsight_recall("XX")` |
| "忘了 XX" | `memory(action='remove', old_text='XX')`（先确认） |

## 核心规则

### 1. 从纠正和反思中学习
- 用户明确纠正时记录
- 自己发现改进时记录
- 绝不从沉默推断
- 3 条相同经验 → 请求用户确认后固化为规则

### 2. 分层存储
- 偏好 → Hermes memory（每次注入）
- 经验/模式 → Hindsight retain（语义检索）
- 具体上下文 → session_search（历史会话）

### 3. 自动升降级
- 模式出现 3 次/7 天 → 从 Hindsight 升级到 memory
- Memory 条目过时 → `memory(action='remove')` 后替换
- 历史会话自然沉淀，不主动删除

### 4. 命名空间隔离
- 小说项目 → `context="novel-writing"`
- 代码开发 → `context="code-dev"`
- 全局偏好 → 无 context 标签
- ⚠️ ADAPTED: 使用 Hindsight 的 tags 参数代替文件命名空间

### 5. 冲突解决
- 项目级 > 全局级
- 同级时最新优先
- 模糊时 → `clarify` 询问

### 6. 透明性
- 每次基于记忆的决策 → 引用来源
- "根据你的偏好（memory: '喜欢简洁回答'），我……"

### 7. 安全边界
- ⚠️ ADAPTED: 原文有 boundaries.md 文件，核心原则内联：
- **绝不存储**: 凭据、健康数据、第三方个人信息
- **绝不推断**: 不从沉默或观察推断偏好
- **绝不联网**: 记忆操作不触发网络请求

## 范围

此 Skill **只做**：
- 从用户纠正和自我反思中学习
- 通过 Hermes memory + Hindsight 存储
- 加载时读取已有记忆

此 Skill **不做**：
- 访问日历、邮件、联系人
- 网络请求
- 从沉默推断偏好
- 修改自己的 SKILL.md

## 与 agent-self-improvement 的关系

本 skill（日常学习）和 agent-self-improvement（正式评估）互补：
- 本 skill：每次对话中自动捕捉纠正和偏好
- agent-self-improvement：定期或按需的深度自我评估
- 本 skill 积累的数据可输入 agent-self-improvement 做分析
