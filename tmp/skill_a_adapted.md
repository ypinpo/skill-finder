---
name: agent-self-improvement
description: Use when evaluating agent performance on past tasks, analyzing failures, or systematically improving skills and workflows through isolated testing. Trigger on: "复盘", "评估 agent", "改进流程", "self-improvement", historical bug analysis, or skill refinement based on failures. Do not use for new feature development.
version: 2.0.0
author: Adapted from v8/v8
license: MIT
metadata:
  hermes:
    tags: [self-improvement, evaluation, meta, workflow]
    related_skills: [systematic-debugging, writing-skills, safe-code-edit]
    adapted_for: hermes
    adapted_from: https://github.com/v8/v8/tree/main/agents/skills/agent-self-improvement
---

# Agent 自我改进工作流

<!-- ADAPTED: 泛化 V8 特定概念（CL/worktree/V8路径），改为通用评估框架 -->

编排 Agent 自我改进会话：在隔离环境中运行任务 → 评估结果 → 识别流程改进点 → 输出可操作的 skill 更新。

## 触发条件

- 分析 Agent 历史行为、评估过往任务表现
- 根据失败经验更新 skill 或规则（元改进）
- 用户要求"复盘"、"评估一下"、"改进流程"
- Agent 自己识别到正在做自我评估时自动激活

## 1. 核心原则

- **隔离**: 子 Agent 必须在独立会话中运行（通过 `delegate_task`），避免上下文污染。⚠️ ADAPTED: 原文用 git worktree，Hermes 改用 delegate_task 天然隔离
- **评估**: 独立的评估阶段分析执行结果
- **分层改进**: 从工具层、Skill 层、编排层三个维度找改进点
- **匿名化**: 更新 skill 时不记录用户具体信息或本地路径
- **抽象化**: 只记录流程原则，不记录具体的测试名、bug ID

## 2. 流程：隔离执行

- **触发**: 新能力验证、Agent 行为 bug、定期基准测试
- **搭建隔离环境**: ⚠️ ADAPTED: 使用 `delegate_task` 创建独立 session
- **启动子 Agent**:
  ```
  delegate_task(
    goal="修复 XXX 问题 / 实现 XXX 功能",
    context="仅提供最少必要上下文，禁止携带外部知识"
  )
  ```
  ⚠️ ADAPTED: 原文依赖 workflow_debugging skill，替换为 systematic-debugging
- 子 Agent 独立工作，完成后返回结果

## 3. 流程：评估

- **触发**: 子 Agent 完成后自动触发
- **启动评估**:
  - 评估 Agent（或主 Agent）接收子 Agent 的日志和结果
  - 提供参考方案作为对比基准
- **差异分析** (⚠️ ADAPTED: 原文为 CL 对比，泛化为通用差异分析):
  - 子 Agent 是否找到相同的根因？
  - 提出的方案是等价的、更好的、还是更差的？
  - 是否走了不必要的捷径或制造了幻觉？
- **分层改进分析**:
  - **工具层**: 是否缺少工具，或误用了现有工具？
  - **Skill 层**: Skill 指令是否不足？是否缺少关键建议？
  - **编排层**: 初始任务描述是否模糊？编排是否失当？

## 4. 可操作输出

- **Skill 更新**: 基于评估结果，提出具体 skill 修改建议（diff 格式）
- **流程改进**: 记录新发现的最佳实践或反模式
- **报告**: 向主 Agent 发送综合报告：执行摘要 + 评估结果 + 改进建议

## 红线

- 不用于新功能开发
- 不在 skill 文件中记录具体用户信息
- 不记录具体测试名或 bug ID
- 保持改进建议抽象通用
