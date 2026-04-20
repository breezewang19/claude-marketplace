# checkpoint-prompts-generator 落库 CSV 生成功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 checkpoint-prompts-generator 新增落库 CSV 生成能力，从审查点 Excel 生成可直接导入系统数据库的 CSV 文件。

**Architecture:** 新增 `generate_db_csv.py` 脚本，内置模板 CSV 数据，读取审查点 Excel 生成占位符模式 Prompt，按 DXCP_WSMC 匹配审查环节替换 PROMPT 字段，输出落库 CSV。SKILL.md 新增生成模式选择步骤。

**Tech Stack:** Python 3, pandas, csv, argparse

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `plugins/checkpoint-prompts-generator/skills/checkpoint-prompts-generator/generate_db_csv.py` | 落库 CSV 生成脚本 |
| Create | `plugins/checkpoint-prompts-generator/skills/checkpoint-prompts-generator/prompts/db_csv_success.md` | 落库 CSV 生成成功提示模板 |
| Modify | `plugins/checkpoint-prompts-generator/skills/checkpoint-prompts-generator/SKILL.md` | 新增 Step 4 生成模式选择 + Step 5/6 扩展 |

---

### Task 1: 创建 generate_db_csv.py 脚本骨架 + 内置模板数据

**Files:**
- Create: `plugins/checkpoint-prompts-generator/skills/checkpoint-prompts-generator/generate_db_csv.py`

- [ ] **Step 1: 创建脚本骨架，包含 argparse 参数解析和内置模板数据**

脚本需要：
1. 从 `aj_dzjz_scyd_prompt_pzxx_202604201447.csv` 提取内置模板数据
2. argparse 命令行参数：`-f`, `-t`, `-o`, `-v`, `--template`
3. 复用现有脚本的 `PLACEHOLDER_TEMPLATE` 和 `AUDIT_POINT_TEMPLATE` 常量

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
落库CSV生成器 - 从审查点Excel生成可直接导入系统数据库的CSV文件

读取审查点Excel，生成占位符模式Prompt，按DXCP_WSMC匹配审查环节替换PROMPT字段，
输出与aj_dzjz_scyd_prompt_pzxx表结构一致的CSV文件。

使用方法：
  python generate_db_csv.py -f "审查点.xlsx"
  python generate_db_csv.py -f "审查点.xlsx" -t "generated_prompts/version_v4.0_R/"
  python generate_db_csv.py -f "审查点.xlsx" --template "模板.csv"
"""

import os
import re
import csv
import textwrap
import argparse
import pandas as pd
from datetime import datetime

# ==============================================================================
# 1. 内置模板数据 (Embedded Template Data)
# ==============================================================================

# 模板CSV的列名
TEMPLATE_HEADERS = [
    "JLBH", "PROMPT", "YXZT", "DXCP_WSMC", "DO_MAIN", "TASK_TYPE",
    "KNOWLEDGE_ID", "PROMPT_ID", "MLXX_ID", "RYLX", "GYXX_JLBH_ID",
    "TASK_PERSON_LX", "SCYD_PZXX_ID", "CORE_PROMPT_ID", "AJ_TYPE"
]

# 内置模板数据 - 从aj_dzjz_scyd_prompt_pzxx_202604201447.csv提取
# 每行是一个字典，PROMPT字段将在运行时被替换
# NOTE: 此数据需要从实际模板CSV文件提取并硬编码
TEMPLATE_DATA = []  # 将在Step 2中填充

# ==============================================================================
# 2. Prompt模板常量 (复用自legal_review_prompt_generator_v4.0_R.py)
# ==============================================================================

PLACEHOLDER_TEMPLATE = """
# 1. 核心任务 (Core Task)
你是一位顶尖的公安法制专家。你的核心任务是根据【核心审查清单与指令】，对【待审查文书】进行严谨的法律审查，并遵循下述审查逻辑。

    核心审查逻辑 (Core Review Logic):
    1.  读取审查任务：逐一处理【核心审查清单与指令】中的每一个"审查单元"对象。首先理解其`审查点名称`、`审查方法与指引`和`审查所需文书类型`。
    2.  定位关键文书：根据`审查所需文书类型`列表中的文书名称，在【待审查文书】（Section #3）的完整列表中查找并定位到对应的文书全文。
    3.  处理文书缺失：
        - 如果`审查所需文书类型`中指定的任何一种文书在【待审查文书】列表中不存在，需要根据具体审查方法的明确要求进行判定：
        * 如果审查方法中明确规定了缺失文书时的判定标准（如"判定为'存在问题'"或"判定为'缺少文书材料'"），则必须遵循审查方法的要求
    4.  提取信息并分析：从已定位文书的全文 `content` 中，根据`审查方法与指引`的说明，提取审查所需的关键信息（如日期、姓名、事由等），并进行分析判断，必须仔细阅读文书的完整内容，不能遗漏任何关键信息。
        - 特别注意：如果涉及日期或时间间隔计算，你必须在思考过程中进行分步推理：首先明确列出起始日期和结束日期，然后进行计算，最后将计算结果与法定期限进行比较。
    5.  定位并引用法律依据：在生成`legal_basis`字段时，你必须在【执法指引】（Section #2）中查找最相关的法律条文。如果找到，必须引用；如果找不到，则`legal_basis`数组中仅包含一个字符串："暂无查询到相关法律法规"。
    6.  生成报告：综合分析结果，并严格按照【输出格式与执行要求】生成报告。

# 2. 执法指引 (Law Enforcement Guidance - Primary Source of Truth)
    【强约束】此部分**仅**用于控制输出结果中`legal_basis`字段的内容。
    - 你**只能**在生成`legal_basis`时阅读并使用【执法指引】。
    - 你**不得**将【执法指引】中的任何内容用于：事实提取、证据判断、期限计算、合规性结论推导、`status`判定、`analysis_details.description`撰写、`analysis_details.recommendation`提出、`referenced_documents`选择等任何"文书审查过程"。
    - 文书审查（`status` / `analysis_details` / `referenced_documents`）的依据只能来自：【核心审查清单与指令】中的审查方法与指引；【待审查文书】（Section #3）中的原文内容。
    - **法律依据及操作实务**

{knowledgeInfos}

# 3. 待审查文书 (Documents for Review)
    这是本次审查所需的所有文书的完整列表。你将根据【核心审查清单与指令】中指定的文书类型，在此处查找对应的文书全文进行审查。

---

{wsxxInfos}

---

# 4. 核心审查清单与指令 (Core Audit Checklist & Instructions)
    此部分用于控制输出结果中的`point_name`、`status`、`analysis_details`（包括`description`和`recommendation`）以及`referenced_documents`字段。你必须严格按照以下清单中的审查单元逐一审查。每个审查单元都详细定义了审查任务，包括审查点名称、审查方法、所需文书类型等，这些信息将直接决定上述字段的输出内容。

    {checklist_content}

# 5. 输出格式与执行要求 (Output Format & Execution Requirements)
    1.  逐项审查：你必须完整地审查【核心审查清单与指令】中的每一个审查单元。
    2.  生成JSON数组：你的最终输出必须是一个JSON数组。输出的JSON对象键名必须使用英文，以便程序解析。
    3.  单个结果对象结构：每个审查结果对象必须严格包含以下英文键名的字段，并遵循指定顺序：
        `point_name`: (string) - 其值必须与【核心审查清单与指令】中`审查点名称`字段的值完全一致。
        `status`: (string) - 必须是以下三种状态之一："存在问题"、"不存在问题"、"缺少文书材料"。此字段的值必须根据【核心审查清单与指令】中的`审查方法与指引`进行判断。
        `analysis_details`: (object) - 此对象的内容必须根据【核心审查清单与指令】中的`审查方法与指引`生成。
            `description`: (string) - 根据【核心审查清单与指令】中的审查方法，对审查结果进行详细描述。在描述中引用文书时，必须且只能使用文书的 `document_name`（例如："根据《受案登记表》显示..."）。严禁在 `description` 字段中出现 `document_id`。如果 `description` 中需要引用文书，只能使用文书的名称（如"受案登记表"、"立案决定书"等），绝不能使用任何数字ID。
            `recommendation`: (string or null) - 根据【核心审查清单与指令】中的审查方法，提供相应的处理建议。
        `referenced_documents`: (array of strings) - 此数组必须包含你在该审查点实际使用的所有文书的 `document_id`。你需要根据【核心审查清单与指令】中`审查所需文书类型`列表里的文书名称，在【待审查文书】列表中找到对应的文书，并将其 `document_id` 填入此数组。
        `legal_basis`: (array of strings) - 此字段的内容必须且只能从【执法指引】（Section #2）中查找相关法律条文。如果找到，必须引用原文；如果找不到，则数组中仅包含一个字符串："暂无查询到相关法律法规"。注意：除`legal_basis`外，任何字段都不得使用【执法指引】内容作为依据。

    5.  输出格式示例 (Example Output):
        此示例展示了当输入指令使用中文键时，你应如何生成符合要求的、使用英文键的输出。
        ```json
        [
        {
            "point_name": "立案时间合规性审查",
            "status": "不存在问题",
            "analysis_details": {
            "description": "根据《受案登记表》和《立案决定书》记载，受案日期与立案决定日期均为2019年7月10日，立案及时，符合办案程序规定。",
            "recommendation": "无需处理"
            },
            "referenced_documents": [
            "00111222",
            "333444555"
            ],
            "legal_basis": [
            "《公安机关办理刑事案件程序规定》第一百七十五条：公安机关接受案件后，经审查，认为有犯罪事实需要追究刑事责任，且属于自己管辖，经县级以上公安机关负责人批准，予以立案。"
            ]
        },
        {
            "point_name": "受案登记信息完整性与一致性审查",
            "status": "存在问题",
            "analysis_details": {
            "description": "《受案登记表》中"报案人姓名"字段填写为"匿名"，但"联系方式"字段又记录了具体的手机号码。该信息存在不一致，可能影响后续联系核实。",
            "recommendation": "建议办案民警核实报案人真实身份信息，并在备注中予以说明或更正。"
            },
            "referenced_documents": [
            "00111222"
            ],
            "legal_basis": [
            "《公安机关办理刑事案件程序规定》第一百七十条：公安机关对于公民报案、控告、举报，都应当接受，问明情况，并制作笔录，经核对无误后，由报案人、控告人、举报人签名或者盖章。"
            ]
        },
        {
            "point_name": "证据收集规范性审查",
            "status": "缺少文书材料",
            "analysis_details": {
            "description": "审查点要求审查《扣押清单》，但在【待审查文书】列表中未找到该文书。无法完成对证据收集规范性的审查。",
            "recommendation": "建议补充提供《扣押清单》等相关文书材料，以便完成审查。"
            },
            "referenced_documents": [],
            "legal_basis": [
            "暂无查询到相关法律法规"
            ]
        }
        ]
        ```

# 6. 输出结果 (Output Result)
    ```json
    [
    // 请在此处生成最终的审查结果
    ]
"""

AUDIT_POINT_TEMPLATE = """     审查点 {point_number}: {point_name}
      审查方法 (提示):
{review_steps}
      审查所需文书类型: {required_documents}"""

# ==============================================================================
# 3. 核心功能函数
# ==============================================================================

def generate_prompts_from_excel(excel_path):
    """从Excel文件生成占位符模式Prompt，返回{审查环节: prompt_text}字典"""
    try:
        df = pd.read_excel(excel_path)
    except FileNotFoundError:
        print(f"错误：找不到文件 '{excel_path}'。")
        return None
    except Exception as e:
        print(f"读取Excel文件时发生错误: {e}")
        return None

    if len(df.columns) < 7:
        print(f"错误：Excel文件列数不足（需要7列，现有{len(df.columns)}列）。")
        return None

    column_names = [
        "审查环节", "审查点名称", "审查方法", "需审查的文书类型",
        "审查文书", "执法指引"
    ]
    df_processed = df.iloc[:, 1:7].copy()
    df_processed.columns = column_names

    df_processed.dropna(subset=['审查环节', '审查点名称'], how='all', inplace=True)
    df_processed = df_processed.fillna({
        '审查环节': '',
        '审查方法': '请根据审查点名称进行相应审查',
        '需审查的文书类型': '不限',
        '执法指引': ''
    })

    df_processed = df_processed[
        (df_processed['审查环节'].str.strip() != '') |
        (df_processed['审查点名称'].str.strip() != '')
    ].copy()

    if df_processed.empty:
        print("错误：处理后的数据为空。")
        return None

    prompts = {}
    grouped_data = df_processed.groupby('审查环节')

    for stage_name, group_df in grouped_data:
        stage_name = str(stage_name).strip()
        if not stage_name:
            continue

        audit_points_list = []
        for i, row in group_df.reset_index(drop=True).iterrows():
            point_name = str(row['审查点名称']).strip()
            if not point_name:
                continue

            raw_method_hint = str(row['审查方法']).strip()
            raw_method_hint = re.sub(r'\n\s*\n\s*\n+', '\n\n', raw_method_hint)
            lines = raw_method_hint.split('\n')
            cleaned_lines = [line.rstrip() for line in lines]
            raw_method_hint = '\n'.join(cleaned_lines).strip()
            indented_method_hint = textwrap.indent(raw_method_hint, ' ' * 9)

            formatted_point = AUDIT_POINT_TEMPLATE.format(
                point_number=i + 1,
                point_name=point_name,
                review_steps=indented_method_hint,
                required_documents=str(row['需审查的文书类型']).strip()
            )
            audit_points_list.append(formatted_point)

        if not audit_points_list:
            continue

        checklist_content = "\n\n".join(audit_points_list)
        final_prompt = PLACEHOLDER_TEMPLATE.replace("{checklist_content}", checklist_content)
        prompts[stage_name] = final_prompt

    return prompts


def load_prompts_from_txt(txt_dir):
    """从已生成的.txt文件读取Prompt，返回{审查环节: prompt_text}字典"""
    prompts = {}
    if not os.path.isdir(txt_dir):
        print(f"警告：目录不存在 '{txt_dir}'")
        return prompts

    for filename in os.listdir(txt_dir):
        if filename.startswith("Prompt_") and filename.endswith(".txt"):
            # 从文件名提取审查环节: Prompt_{审查环节}_{version}.txt
            match = re.match(r"Prompt_(.+?)_v\d+\.\d+_\w+\.txt", filename)
            if match:
                stage_name = match.group(1)
                filepath = os.path.join(txt_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    prompts[stage_name] = f.read()

    return prompts


def load_template_data(template_path=None):
    """加载模板数据，优先使用外部文件，否则使用内置数据"""
    if template_path and os.path.exists(template_path):
        rows = []
        with open(template_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
        return rows
    else:
        return TEMPLATE_DATA


def match_stage(dxcp_wsmc, stage_names):
    """
    从DXCP_WSMC匹配审查环节。

    DXCP_WSMC格式：案件类型-审查环节-审查点名称
    匹配策略：
    1. 精确匹配：第二段与stage_names完全一致
    2. 包含匹配：stage_name包含在第二段中，或第二段包含在stage_name中
    """
    parts = dxcp_wsmc.split('-')
    if len(parts) < 2:
        return None

    second_segment = parts[1]

    # 精确匹配
    for stage_name in stage_names:
        if stage_name == second_segment:
            return stage_name

    # 包含匹配
    for stage_name in stage_names:
        if stage_name in second_segment or second_segment in stage_name:
            return stage_name

    return None


def generate_db_csv(excel_path, output_dir, version, txt_dir=None, template_path=None):
    """生成落库CSV文件"""
    # 1. 获取Prompt内容
    if txt_dir:
        print(f"从目录读取已有Prompt: {txt_dir}")
        prompts = load_prompts_from_txt(txt_dir)
    else:
        print(f"从Excel生成Prompt: {excel_path}")
        prompts = generate_prompts_from_excel(excel_path)

    if prompts is None or not prompts:
        print("错误：无法获取Prompt内容。")
        return

    print(f"共 {len(prompts)} 个审查环节的Prompt")

    # 2. 加载模板数据
    template_rows = load_template_data(template_path)
    if not template_rows:
        print("错误：模板数据为空。")
        return

    print(f"模板共 {len(template_rows)} 行")

    # 3. 匹配并替换PROMPT字段
    matched_count = 0
    unmatched = []

    for row in template_rows:
        dxcp_wsmc = row.get('DXCP_WSMC', '')
        matched_stage = match_stage(dxcp_wsmc, prompts.keys())

        if matched_stage:
            row['PROMPT'] = prompts[matched_stage]
            matched_count += 1
        else:
            unmatched.append(dxcp_wsmc)

    # 4. 输出CSV
    versioned_output_dir = os.path.join(output_dir, f"version_{version}")
    os.makedirs(versioned_output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    output_filename = f"aj_dzjz_scyd_prompt_pzxx_{timestamp}.csv"
    output_path = os.path.join(versioned_output_dir, output_filename)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=TEMPLATE_HEADERS)
        writer.writeheader()
        writer.writerows(template_rows)

    # 5. 输出统计
    total = len(template_rows)
    print(f"\n✅ 落库CSV已生成: {output_path}")
    print(f"   匹配成功: {matched_count}/{total} 行")
    if unmatched:
        print(f"   未匹配: {len(unmatched)} 行（保持模板原值）")
        for u in unmatched:
            print(f"     • {u}")

    return output_path


# ==============================================================================
# 4. 主程序入口
# ==============================================================================

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='落库CSV生成器 - 从审查点Excel生成落库CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python generate_db_csv.py -f "审查点.xlsx"
  python generate_db_csv.py -f "审查点.xlsx" -t "generated_prompts/version_v4.0_R/"
  python generate_db_csv.py -f "审查点.xlsx" --template "模板.csv"
        """
    )

    parser.add_argument('-f', '--file', type=str, required=True,
                        help='审查点Excel文件路径（必需）')
    parser.add_argument('-t', '--txt-dir', type=str, default=None,
                        help='已生成的.txt Prompt目录（可选，提供则跳过Prompt生成）')
    parser.add_argument('-o', '--output', type=str, default='generated_prompts',
                        help='输出目录（默认: generated_prompts）')
    parser.add_argument('-v', '--version', type=str, default='v4.0_R',
                        help='版本信息（默认: v4.0_R）')
    parser.add_argument('--template', type=str, default=None,
                        help='模板CSV路径（可选，默认使用内置模板）')

    return parser.parse_args()


def main():
    args = parse_arguments()

    print("=" * 60)
    print(f"📋 落库CSV生成器 {args.version}")
    print("=" * 60)
    print(f"📄 Excel文件: {args.file}")
    if args.txt_dir:
        print(f"📁 Prompt目录: {args.txt_dir}")
    print(f"📁 输出目录: {args.output}")
    print()

    if not os.path.exists(args.file):
        print(f"⚠️  找不到Excel文件: {args.file}")
        return

    generate_db_csv(args.file, args.output, args.version, args.txt_dir, args.template)

    print("\n" + "=" * 60)
    print("🎉 落库CSV已生成完毕！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已被用户中断。")
```

- [ ] **Step 2: 从模板CSV提取数据并填充TEMPLATE_DATA**

运行以下命令从模板CSV提取数据，生成Python字典列表：

```bash
python -c "
import csv, json
with open('D:/projects/claude-marketplace/temp/aj_dzjz_scyd_prompt_pzxx_202604201447.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = []
    for row in reader:
        r = dict(row)
        # 保留PROMPT原始内容
        rows.append(r)
    # 输出为Python代码
    print('TEMPLATE_DATA = [')
    for r in rows:
        print('    {')
        items = list(r.items())
        for i, (k, v) in enumerate(items):
            comma = ',' if i < len(items) - 1 else ''
            print(f'        {repr(k)}: {repr(v)}{comma}')
        print('    },')
    print(']')
" > template_data.py
```

然后将生成的 `template_data.py` 中的 `TEMPLATE_DATA` 列表复制到 `generate_db_csv.py` 的 `TEMPLATE_DATA` 变量中。

- [ ] **Step 3: 验证脚本可运行**

```bash
cd D:/projects/claude-marketplace/plugins/checkpoint-prompts-generator/skills/checkpoint-prompts-generator
python generate_db_csv.py -h
```

Expected: 显示帮助信息，无报错

- [ ] **Step 4: Commit**

```bash
git add plugins/checkpoint-prompts-generator/skills/checkpoint-prompts-generator/generate_db_csv.py
git commit -m "feat(checkpoint-prompts-generator): add generate_db_csv.py script"
```

---

### Task 2: 创建 db_csv_success.md 提示模板

**Files:**
- Create: `plugins/checkpoint-prompts-generator/skills/checkpoint-prompts-generator/prompts/db_csv_success.md`

- [ ] **Step 1: 创建成功提示模板**

```markdown
# 落库CSV生成成功提示

---

📊 落库CSV已生成！

📁 输出位置：[当前目录]/generated_prompts/version_v4.0_R/aj_dzjz_scyd_prompt_pzxx_{timestamp}.csv
✅ 匹配成功：X/Y 行
⚠️ 未匹配：Z 行（保持模板原值）
  • 未匹配项：[DXCP_WSMC 列表]

💡 提示：生成的CSV可直接导入系统数据库。未匹配的行保持模板原PROMPT值，请确认是否需要手动补充。
```

- [ ] **Step 2: Commit**

```bash
git add plugins/checkpoint-prompts-generator/skills/checkpoint-prompts-generator/prompts/db_csv_success.md
git commit -m "feat(checkpoint-prompts-generator): add db_csv_success.md prompt template"
```

---

### Task 3: 修改 SKILL.md 新增生成模式选择和落库CSV生成步骤

**Files:**
- Modify: `plugins/checkpoint-prompts-generator/skills/checkpoint-prompts-generator/SKILL.md`

- [ ] **Step 1: 在 Step 3a 之后插入 Step 4（生成模式选择）**

在现有 `## Step 3a: Validation Passed` 的确认逻辑之后，将原来的"是否继续生成？(y/n)"改为先询问生成模式：

找到 SKILL.md 中 Step 3a 的内容，将：

```
是否继续生成？(y/n)
```

替换为：

```
请选择生成模式：
A) 仅生成 .txt Prompt 文件
B) 生成 .txt + 落库 CSV（推荐）
C) 仅生成落库 CSV

请输入选项 (A/B/C)：
```

- User inputs `A` → proceed to Step 5 (existing logic only)
- User inputs `B` → proceed to Step 5 (existing logic + generate_db_csv.py)
- User inputs `C` → skip Step 5 txt generation, call generate_db_csv.py directly

- [ ] **Step 2: 扩展 Step 5 执行逻辑**

在 Step 5 的现有执行逻辑后，增加模式 B/C 的处理：

在 `## Step 5: Execute Python Script` 末尾追加：

```markdown
## Step 5b: Execute DB CSV Generator (Only for Mode B/C)

When user selected Mode B or C in Step 4, execute the following after Step 5 (Mode B) or instead of Step 5 (Mode C):

```python
import subprocess
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
db_csv_script = os.path.join(script_dir, "generate_db_csv.py")

cmd = [
    "python",
    db_csv_script,
    "-f", excel_path,
    "-o", "generated_prompts",
    "-v", "v4.0_R"
]

# If Mode C and .txt files already exist from a previous run:
if txt_dir_path:
    cmd.extend(["-t", txt_dir_path])

result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    encoding='utf-8'
)
```
```

- [ ] **Step 3: 扩展 Step 6a 输出结果**

在 `## Step 6a: Execution Success` 的成功信息后追加模式 B/C 的输出：

```markdown
For Mode B/C, additionally display the db_csv_success.md content:

```
📊 落库CSV已生成！

📁 输出位置：[当前目录]/generated_prompts/version_v4.0_R/aj_dzjz_scyd_prompt_pzxx_{timestamp}.csv
✅ 匹配成功：X/Y 行
⚠️ 未匹配：Z 行（保持模板原值）
  • 未匹配项：[DXCP_WSMC 列表]
```
```

- [ ] **Step 4: 更新 Reference Files 和 Technical Constraints**

在 `## Reference Files` 中追加：

```markdown
- `prompts/db_csv_success.md` - Output prompt after successful DB CSV generation
```

在 `## Technical Constraints` 中追加：

```markdown
8. **DB CSV Script**: Path relative to Skill directory `generate_db_csv.py`
9. **DB CSV Template**: Embedded in `generate_db_csv.py` as `TEMPLATE_DATA`, sourced from `aj_dzjz_scyd_prompt_pzxx_202604201447.csv`
10. **DB CSV Matching**: `DXCP_WSMC` second segment (split by `-`) matched against Excel B column
11. **DB CSV Output**: `aj_dzjz_scyd_prompt_pzxx_{timestamp}.csv` in versioned output directory
```

- [ ] **Step 5: 更新 Error Handling Flow 图**

在现有流程图中追加模式分支：

```
用户输入文件路径
        ↓
    验证文件
        ↓
    ┌─── 验证通过 ───┐
    ↓               ↓
  步骤3a         步骤3b
(确认模式)     (显示错误选项)
    ↓               ↓
  选择模式         1/2
  A/B/C            ↓
    ↓             1 → 修复并继续
  A → 执行脚本   2 → 中止
  B → 执行脚本+DB CSV
  C → 仅执行DB CSV
        ↓
    执行脚本
        ↓
    ┌─── 成功 ───┐
    ↓           ↓
  success.md  error_diagnosis.md
    ↓
  (Mode B/C: db_csv_success.md)
```

- [ ] **Step 6: Commit**

```bash
git add plugins/checkpoint-prompts-generator/skills/checkpoint-prompts-generator/SKILL.md
git commit -m "feat(checkpoint-prompts-generator): add DB CSV generation mode to SKILL.md"
```

---

### Task 4: 端到端验证

**Files:** None (validation only)

- [ ] **Step 1: 用示例Excel测试 generate_db_csv.py**

```bash
cd D:/projects/claude-marketplace/plugins/checkpoint-prompts-generator/skills/checkpoint-prompts-generator
python legal_review_prompt_generator_v4.0_R.py --interactive-file
# 先生成示例Excel
python legal_review_prompt_generator_v4.0_R.py -f config.xlsx
# 然后测试落库CSV生成
python generate_db_csv.py -f config.xlsx -o test_output -v v4.0_R
```

Expected: 生成 `test_output/version_v4.0_R/aj_dzjz_scyd_prompt_pzxx_*.csv`，控制台显示匹配统计

- [ ] **Step 2: 验证生成的CSV结构正确**

```bash
python -c "
import csv
import glob
files = glob.glob('test_output/version_v4.0_R/aj_dzjz_scyd_prompt_pzxx_*.csv')
if files:
    with open(files[0], 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        print(f'Headers: {reader.fieldnames}')
        rows = list(reader)
        print(f'Rows: {len(rows)}')
        # Check PROMPT field is not empty for matched rows
        non_empty = sum(1 for r in rows if r['PROMPT'].strip())
        print(f'Non-empty PROMPT: {non_empty}/{len(rows)}')
else:
    print('No CSV files found!')
"
```

Expected: Headers 与 TEMPLATE_HEADERS 一致，部分行的 PROMPT 被替换为实际内容

- [ ] **Step 3: 测试 --template 参数（外部模板）**

```bash
python generate_db_csv.py -f config.xlsx -o test_output2 -v v4.0_R --template "D:/projects/claude-marketplace/temp/aj_dzjz_scyd_prompt_pzxx_202604201447.csv"
```

Expected: 使用外部模板，结果与内置模板一致

- [ ] **Step 4: 清理测试输出**

```bash
rm -rf test_output test_output2
```

- [ ] **Step 5: Commit (if any fixes were needed)**

If any fixes were applied during testing:

```bash
git add -A
git commit -m "fix(checkpoint-prompts-generator): fix issues found during e2e testing"
```

---

### Task 5: 同步更新已安装的插件缓存

**Files:** None (cache sync only)

- [ ] **Step 1: 将新增文件复制到插件缓存目录**

```bash
cp plugins/checkpoint-prompts-generator/skills/checkpoint-prompts-generator/generate_db_csv.py ~/.claude/plugins/cache/yrwang45-marketplace/checkpoint-prompts-generator/1.0.0/skills/checkpoint-prompts-generator/
cp plugins/checkpoint-prompts-generator/skills/checkpoint-prompts-generator/prompts/db_csv_success.md ~/.claude/plugins/cache/yrwang45-marketplace/checkpoint-prompts-generator/1.0.0/skills/checkpoint-prompts-generator/prompts/
cp plugins/checkpoint-prompts-generator/skills/checkpoint-prompts-generator/SKILL.md ~/.claude/plugins/cache/yrwang45-marketplace/checkpoint-prompts-generator/1.0.0/skills/checkpoint-prompts-generator/
```

- [ ] **Step 2: 验证缓存文件完整**

```bash
ls -laR ~/.claude/plugins/cache/yrwang45-marketplace/checkpoint-prompts-generator/1.0.0/
```

Expected: 包含 generate_db_csv.py, prompts/db_csv_success.md, 更新后的 SKILL.md
