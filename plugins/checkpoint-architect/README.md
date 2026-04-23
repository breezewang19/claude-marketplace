# checkpoint-architect

审查点构建助手 - 引导式对话创建合规审查点内容。

## 功能特性

- 引导式对话，无需技术背景
- 三种模式：快速 / 引导 / 批量
- 5 种审查模式模板：文书完整性、时限合规性、信息一致性、程序合规性、自定义
- 自动验证 + 自动修正
- 生成可视化流程图（Mermaid + ASCII）
- 推荐信息点清单（复用系统文书要素定义）
- 支持行政/刑事两种案件类型
- 输出文件包含免责声明

## 使用方式

安装后，在 Claude Code 中输入 `/checkpoint-architect` 即可启动。

## 文件结构

```
skills/checkpoint-architect/
├── SKILL.md                  ← 主流程（8 步）
├── input-parsing.md          ← 输入解析与验证
├── guided-questioning.md     ← 引导提问框架
├── diagram-generation.md     ← 流程图生成规则
├── review-iteration.md       ← 审查迭代逻辑
├── checkpoint-templates.md   ← 5 种审查模式模板
└── checkpoint-validator.md   ← 内容验证规则
data/
├── 【行政】...csv             ← 行政案件文书要素定义
└── 【刑事】...csv             ← 刑事案件文书要素定义
```

## 版本历史

- v2.2.0：拆分 SKILL.md 为子模块，优化交互体验，支持行政/刑事案件，移除硬编码路径
- v2.1.0：复用系统文书要素定义生成审查步骤和推荐信息点
- v2.0.0：信息点推断、引导模式持续追问、可视化流程图
- v1.0.0：初始版本