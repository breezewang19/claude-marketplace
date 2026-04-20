# checkpoint-prompts-generator 落库 CSV 生成功能设计

## 背景

`checkpoint-prompts-generator` 当前只能从 Excel/CSV 生成 `.txt` Prompt 文件。需要增加落库 CSV 生成能力，使生成的 Prompt 可以直接导入 V1.1.1 系统数据库。

## 现有流程

```
用户提供 Excel → Python 脚本生成 .txt Prompt 文件（占位符模式）
```

- 占位符模式：执法指引用 `{knowledgeInfos}`，文书用 `{wsxxInfos}`
- 输出：`generated_prompts/version_v4.0_R/Prompt_{审查环节}_{version}.txt`

## 目标流程

```
用户提供 Excel → 选择生成模式 →
  A) 仅生成 .txt（现有）
  B) 生成 .txt + 落库 CSV
  C) 仅生成落库 CSV
```

落库 CSV 结构与 `aj_dzjz_scyd_prompt_pzxx` 表一致，15 个字段，只替换 PROMPT 字段。

## 落库 CSV 字段

| 字段 | 说明 | 处理方式 |
|------|------|----------|
| JLBH | 记录编号 | 保持模板原值 |
| PROMPT | 完整 Prompt 文本 | **替换**：根据 DXCP_WSMC 匹配审查环节，填入生成的 Prompt |
| YXZT | 有效状态 | 保持模板原值 |
| DXCP_WSMC | 对象审查点文书名称 | 保持模板原值，用于匹配审查环节 |
| DO_MAIN | 主域 | 保持模板原值 |
| TASK_TYPE | 任务类型 | 保持模板原值 |
| KNOWLEDGE_ID | 知识 ID | 保持模板原值 |
| PROMPT_ID | Prompt ID | 保持模板原值 |
| MLXX_ID | 目录信息 ID | 保持模板原值 |
| RYLX | 人员类型 | 保持模板原值 |
| GYXX_JLBH_ID | 公用信息记录编号 ID | 保持模板原值 |
| TASK_PERSON_LX | 任务人员类型 | 保持模板原值 |
| SCYD_PZXX_ID | 审查要点配置信息 ID | 保持模板原值 |
| CORE_PROMPT_ID | 核心 Prompt ID | 保持模板原值 |
| AJ_TYPE | 案件类型 | 保持模板原值 |

## generate_db_csv.py 设计

### 输入

- 审查点 Excel 文件路径（B-G列：审查环节/审查点名称/审查方法/文书类型/审查文书/执法指引）
- 可选：已生成的 .txt Prompt 文件目录（提供则直接读取，否则从 Excel 生成）

### 内置模板

从 `aj_dzjz_scyd_prompt_pzxx_202604201447.csv` 提取，作为 Python 字典列表硬编码在脚本中。每行包含 15 个字段的原始值。

### 处理逻辑

1. 读取审查点 Excel，按审查环节（B列）分组
2. 对每个审查环节，生成占位符模式 Prompt（执法指引用 `{knowledgeInfos}`，文书用 `{wsxxInfos}`）
3. 读取内置模板数据
4. 遍历模板每行：
   - 从 `DXCP_WSMC` 提取审查环节关键词（取 `-` 分隔的最后一段，或整段模糊匹配）
   - 与 Excel B列审查环节做匹配
   - 匹配成功 → 替换该行的 PROMPT 字段为生成的 Prompt 内容
   - 匹配失败 → 保持模板原值，记录未匹配项
5. 输出新 CSV 文件

### 匹配规则

`DXCP_WSMC` 格式示例：`"行政-受(立)案情况-受案登记表规范性审查"`

匹配策略：
1. 精确匹配：`DXCP_WSMC` 中 `-` 分隔的第二段与 Excel B列完全一致
2. 模糊匹配：如果精确匹配失败，检查 B列值是否包含在 `DXCP_WSMC` 中
3. 未匹配：保持原 PROMPT 值，在日志中输出警告

### 命令行参数

```
python generate_db_csv.py
  -f, --file         审查点 Excel 文件路径（必需）
  -t, --txt-dir      已生成的 .txt Prompt 目录（可选，提供则跳过 Prompt 生成）
  -o, --output       输出目录（默认：generated_prompts）
  -v, --version      版本信息（默认：v4.0_R）
  --template         模板 CSV 路径（可选，默认使用内置模板）
```

### 输出

- `generated_prompts/version_v4.0_R/aj_dzjz_scyd_prompt_pzxx_{timestamp}.csv`
- 控制台输出：匹配统计（成功/失败数量）、未匹配的 DXCP_WSMC 列表

## SKILL.md 变更

### Step 2 扩展：文件收集

用户只需提供审查点 Excel 文件。模板 CSV 已内置，无需用户提供。

### Step 4 新增：生成模式选择

在 Step 3（文件验证通过）之后，询问用户选择生成模式：

```
请选择生成模式：
A) 仅生成 .txt Prompt 文件
B) 生成 .txt + 落库 CSV（推荐）
C) 仅生成落库 CSV

请输入选项 (A/B/C)：
```

- 默认推荐 B
- 选择 A → 执行现有逻辑（Step 5 现有）
- 选择 B → 执行现有逻辑 + 调用 generate_db_csv.py
- 选择 C → 仅调用 generate_db_csv.py

### Step 5 扩展：执行生成

模式 B/C 时，在现有 Step 5 完成后（或跳过），调用：

```python
cmd = [
    "python",
    script_path,  # generate_db_csv.py
    "-f", excel_path,
    "-o", "generated_prompts",
    "-v", "v4.0_R"
]

# 如果模式 C 且已有 .txt 文件：
cmd.extend(["-t", txt_dir_path])
```

### Step 6 扩展：输出结果

模式 B/C 时，在现有成功信息后追加：

```
📊 落库 CSV 已生成！

📁 输出位置：[当前目录]/generated_prompts/version_v4.0_R/aj_dzjz_scyd_prompt_pzxx_{timestamp}.csv
✅ 匹配成功：X/Y 行
⚠️ 未匹配：Z 行（保持模板原值）
  • 未匹配项：[DXCP_WSMC 列表]
```

## 新增文件

| 文件 | 说明 |
|------|------|
| `generate_db_csv.py` | 落库 CSV 生成脚本 |
| `prompts/db_csv_success.md` | 落库 CSV 生成成功提示模板 |

## 不变项

- `legal_review_prompt_generator_v4.0_R.py` 不修改
- 现有 Step 1/3 逻辑不变
- 占位符模式为默认（执法指引 `{knowledgeInfos}`，文书 `{wsxxInfos}`）
