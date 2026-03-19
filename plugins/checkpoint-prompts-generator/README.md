# checkpoint-prompts-generator

审查要点Prompt生成器 - 帮助非技术人员通过对话调用法律审查Prompt生成脚本，从Excel/CSV文件生成法律审查长提词。

## 功能说明

本插件帮助用户通过交互式对话，将包含审查数据的Excel/CSV文件转换为法律审查Prompt。

## 使用方式

在Claude Code中输入：

```
/checkpoint-prompts-generator
```

## 输入文件格式

插件需要用户提供包含以下列的Excel文件：
- B列：审查环节
- C列：审查点名称
- D列：审查方法
- E列：需审查的文书类型
- F列：审查文书
- G列：执法指引

## 输出

生成的文件位于 `generated_prompts/version_v4.0_R/` 目录下，每个审查环节对应一个Prompt文件。

## 目录结构

```
checkpoint-prompts-generator/
├── .claude-plugin/
│   └── plugin.json          # 插件元数据
├── skills/
│   └── checkpoint-prompts-generator/
│       ├── SKILL.md                              # 主技能文件
│       ├── legal_review_prompt_generator_v4.0_R.py  # Python生成器脚本
│       └── prompts/
│           ├── validation.md     # 文件验证失败提示
│           ├── error_diagnosis.md # 错误诊断与修复选项
│           └── success.md        # 生成成功提示
└── README.md
```
