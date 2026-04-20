#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法律审查Prompt生成器 v4.0_R

这个脚本从Excel文件读取审查数据，并为每个"审查环节"生成一个独立的prompt文本文件。
适配用户实际Excel文件格式：
B列（审查环节）、C列（审查要点内容）、D列（详细计算规则）、
E列（需审查的文书类型）、F列（审查文书）、G列（法律依据及操作实务）

使用方法：
1. 准备包含审查数据的Excel文件。
2. 运行脚本（支持命令行参数）：
   - 基本用法：python legal_review_prompt_generator_v3.0.py
   - 指定文件：python legal_review_prompt_generator_v3.0.py -f "我的数据.xlsx"
   - 完整参数：python legal_review_prompt_generator_v3.0.py -f "数据.xlsx" -o "输出文件夹" -v "v4.0_R"
   - 查看帮助：python legal_review_prompt_generator_v3.0.py -h
"""

import os
import re
import textwrap
import pandas as pd
import argparse

# ==============================================================================
# 1. 常量定义 (Constants)
# ==============================================================================

# 主要的 Prompt 结构模板
PROMPT_TEMPLATE = """
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
    - 文书审查（`status` / `analysis_details` / `referenced_documents`）的依据只能来自：①【核心审查清单与指令】中的审查方法与指引；②【待审查文书】（Section #3）中的原文内容。
    - 法律依据及操作实务
    {enforcement_guidance}

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

    4.  输出格式示例 (Example Output):
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
            "《公安机关办理刑事案件程序规定》第一百七十五条：公安机关接受案件后，经审查，认为有犯罪事实需要追究刑事责任，且属于自己管辖的，经县级以上公安机关负责人批准，予以立案。"
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

# 占位符模式的 Prompt 模板（只包含审查点，执法指引和待审查文书使用占位符）
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
            "《公安机关办理刑事案件程序规定》第一百七十五条：公安机关接受案件后，经审查，认为有犯罪事实需要追究刑事责任，且属于自己管辖的，经县级以上公安机关负责人批准，予以立案。"
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

# 单个审查点的格式化模板
AUDIT_POINT_TEMPLATE = """     审查点 {point_number}: {point_name}
      审查方法 (提示):
{review_steps}
      审查所需文书类型: {required_documents}"""


# ==============================================================================
# 2. 辅助功能函数 (Helper Functions)
# ==============================================================================

# ==============================================================================
# 3. 核心功能函数 (Core Functions)
# ==============================================================================

def generate_prompts_from_excel(excel_path, output_dir, version, use_excel_guidance, use_placeholder_mode=False):
    """
    从Excel文件生成审查Prompt。

    Args:
        excel_path (str): 包含审查数据的Excel文件路径。
        output_dir (str): 存放生成文件的输出目录名。
        version (str): 版本信息，用于命名。
        use_excel_guidance (bool): 是否使用Excel中的执法指引。
        use_placeholder_mode (bool): 是否使用占位符模式（只生成审查点，执法指引和待审查文书使用占位符）。
    """
    # 1. 读取并预处理数据文件（支持Excel和CSV）
    try:
        ext = os.path.splitext(excel_path)[1].lower()
        if ext == '.csv':
            df = pd.read_csv(excel_path, encoding='utf-8')
        else:
            df = pd.read_excel(excel_path)
    except FileNotFoundError:
        print(f"错误：找不到文件 '{excel_path}'。请检查路径是否正确。")
        return
    except Exception as e:
        print(f"读取Excel文件时发生错误: {e}")
        return

    if len(df.columns) < 7:
        print(f"错误：Excel文件列数不足（需要7列，现有{len(df.columns)}列）。")
        print(f"当前文件列名: {list(df.columns)}")
        return

    # 使用标准名称重命名列
    column_names = [
        "审查环节", "审查点名称", "审查方法", "需审查的文书类型",
        "审查文书", "执法指引"
    ]
    # 使用.copy()避免pandas警告
    df_processed = df.iloc[:, 1:7].copy()
    df_processed.columns = column_names

    # 2. 数据清理
    df_processed.dropna(subset=['审查环节', '审查点名称'], how='all', inplace=True)
    # 使用推荐的语法避免FutureWarning
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
        print("错误：处理后的数据为空，请检查Excel文件内容。")
        return

    # 3. 创建输出目录
    versioned_output_dir = os.path.join(output_dir, f"version_{version}")
    os.makedirs(versioned_output_dir, exist_ok=True)

    # 4. 按"审查环节"分组并生成Prompt文件
    grouped_data = df_processed.groupby('审查环节')
    print(f"共发现 {len(grouped_data)} 个审查环节，开始生成 Prompts...")

    for stage_name, group_df in grouped_data:
        stage_name = str(stage_name).strip()
        if not stage_name:
            continue

        print(f"\n正在处理审查环节: 「{stage_name}」")
        audit_points_list = []

        # 遍历环节下的所有审查点
        for i, row in group_df.reset_index(drop=True).iterrows():
            point_name = str(row['审查点名称']).strip()
            if not point_name:
                continue

            # 准备并格式化审查方法文本的缩进
            raw_method_hint = str(row['审查方法']).strip()
            # 清理内部多余空行：将多个连续空行压缩为单个空行
            raw_method_hint = re.sub(r'\n\s*\n\s*\n+', '\n\n', raw_method_hint)
            # 清理行首行尾空白，但保留单行内容
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
            print(f"  -> ⚠️ 审查环节「{stage_name}」无有效审查点，已跳过。")
            continue

        # 各审查点之间空一行
        checklist_content = "\n\n".join(audit_points_list)

        # 根据占位符模式选择模板
        if use_placeholder_mode:
            # 占位符模式：使用占位符模板，执法指引和待审查文书都使用占位符
            final_prompt = PLACEHOLDER_TEMPLATE.replace("{checklist_content}", checklist_content)
            # 占位符模式中，{knowledgeInfos} 和 {wsxxInfos} 已经内置在模板中，不需要额外处理
        else:
            # 正常模式：使用标准模板，需要处理执法指引和待审查文书
            final_prompt = PROMPT_TEMPLATE.replace("{checklist_content}", checklist_content)

            # 处理执法指引
            enforcement_guidance = "{knowledgeInfos}"  # 默认使用占位符
            # 查找第一个非空的执法指引作为该环节的通用指引
            # 使用.copy()避免pandas警告
            guidance_series = group_df['执法指引'].copy()
            guidance_series = guidance_series.astype(str)  # 确保转换为字符串类型
            guidance_series = guidance_series.str.strip()
            guidance_series = guidance_series.replace('', pd.NA)
            guidance_series = guidance_series.replace('nan', pd.NA)  # 处理 'nan' 字符串
            guidance_series = guidance_series.replace('None', pd.NA)  # 处理 'None' 字符串
            valid_guidances = guidance_series.dropna()
            if not valid_guidances.empty:
                raw_guidance = valid_guidances.iloc[0]
                # 再次检查是否真的是有效内容（不是空字符串或只有空白字符）
                if raw_guidance and raw_guidance.strip():
                    # 格式化执法指引：将内容按行分割，每行添加正确的缩进
                    # 如果行已经包含 -【法律依据】或【操作实务】，则添加8个空格前缀
                    # 如果行是续行（不以【开头），则添加9个空格前缀
                    guidance_lines = raw_guidance.split('\n')
                    formatted_lines = []
                    for line in guidance_lines:
                        line = line.strip()
                        if not line:
                            continue
                        # 如果行已经以 -【法律依据】开头，直接添加8个空格
                        if line.startswith('-【法律依据】'):
                            formatted_lines.append('        ' + line)
                        # 如果行以【法律依据】开头（没有-），添加8个空格和-
                        elif line.startswith('【法律依据】'):
                            formatted_lines.append('        -' + line)
                        # 如果行以【操作实务】开头，添加8个空格
                        elif line.startswith('【操作实务】'):
                            formatted_lines.append('        ' + line)
                        # 其他情况，可能是续行（不以【开头），添加9个空格
                        else:
                            formatted_lines.append('         ' + line)
                    if formatted_lines:  # 确保有格式化后的内容
                        enforcement_guidance = '\n'.join(formatted_lines)
                    elif raw_guidance.strip():  # 如果没有格式化行但有原始内容，使用原始内容
                        enforcement_guidance = raw_guidance.strip()

            final_prompt = final_prompt.replace("{enforcement_guidance}", enforcement_guidance)

        # 5. 写入文件
        safe_filename = "".join(
            c for c in stage_name if c.isalnum() or c in ['_', '-', '(', ')']
        ) or f"stage_{len(audit_points_list)}_points"

        output_filename = f"Prompt_{safe_filename}_{version}.txt"
        output_path = os.path.join(versioned_output_dir, output_filename)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_prompt)
            print(f"  -> ✅ 已成功生成文件: {output_path}")
        except Exception as e:
            print(f"  -> ❌ 写入文件时发生错误: {e}")


def create_sample_excel(filename):
    """
    创建一个包含示例数据的Excel文件，用于演示格式。
    """
    sample_data = {
        '审查类别': ['程序审查', '程序审查', '程序审查', '程序审查', '办案期限'],
        '审查环节': ['受(立)案情况', '受(立)案情况', '证据收集', '证据收集', '办案期限'],
        '审查要点内容': [
            '是否及时受案', '是否及时立案', '物证收集是否规范',
            '证人证言是否合法', '办案期限是否超期'
        ],
        '详细计算规则': [
            '受害人的询问笔录中的报案时间与受案登记表的受案审批时间相差是否大于1天',
            '立案决定书的审批时间是否在受案登记表的审批时间的30日之内',
            '检查物证的收集、保管、鉴定程序是否规范',
            '审查证人证言的取得程序是否合法，内容是否真实',
            '核查各个办案环节的时间节点是否符合法定期限要求'
        ],
        '需审查的文书类型': [
            '受案登记表, 询问笔录', '受案登记表, 立案决定书', '扣押清单',
            '询问笔录', '案件流程表'
        ],
        '审查文书': ['受案登记表', '立案决定书', '扣押清单', '询问笔录', '案件流程表'],
        '法律依据及操作实务': [
            '【法律依据】《中华人民共和国刑事诉讼法》第一百零八条第三款',
            '【法律依据】《中华人民共和国刑事诉讼法》第一百一十条',
            '【法律依据】《刑事诉讼法》第52-58条关于证据的规定',
            '【法律依据】《刑事诉讼法》第60-62条关于证人证言的规定',
            '【法律依据】《刑事诉讼法》第154-159条关于办案期限的规定'
        ]
    }

    # 确保所有列表长度一致
    max_len = max(len(v) for v in sample_data.values())
    for k, v in sample_data.items():
        if len(v) < max_len:
            sample_data[k].extend([''] * (max_len - len(v)))

    df = pd.DataFrame(sample_data)
    df.to_excel(filename, index=False)
    print(f"\n✅ 已创建示例Excel文件: {filename}")
    print("请参考此文件格式准备您的数据。注意脚本会读取B到G列。")


# ==============================================================================
# 3. 主程序入口 (Main Execution)
# ==============================================================================

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='法律审查Prompt生成器 - 从Excel文件生成审查Prompt',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python legal_review_prompt_generator_v3.0.py
  python legal_review_prompt_generator_v3.0.py -f "我的数据.xlsx"
  python legal_review_prompt_generator_v3.0.py -f "数据.xlsx" -o "输出文件夹" -v "v3.0"
  python legal_review_prompt_generator_v3.0.py -f "数据.xlsx" --no-guidance
  python legal_review_prompt_generator_v3.0.py -f "数据.xlsx" --placeholder-mode
  python legal_review_prompt_generator_v3.0.py --interactive
  python legal_review_prompt_generator_v3.0.py --interactive-file
        """
    )

    parser.add_argument(
        '-f', '--file',
        type=str,
        default='config.xlsx',
        help='Excel文件路径 (默认: config.xlsx)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='generated_prompts',
        help='输出文件夹名称 (默认: generated_prompts)'
    )

    parser.add_argument(
        '-v', '--version',
        type=str,
        default='v4.0_R',
        help='版本信息 (默认: v4.0_R)'
    )

    parser.add_argument(
        '--no-guidance',
        action='store_true',
        help='不使用Excel中的执法指引，留空待自定义'
    )

    parser.add_argument(
        '--placeholder-mode',
        '--minimal',
        dest='placeholder_mode',
        action='store_true',
        help='使用占位符模式：只生成审查点，执法指引和待审查文书使用占位符 {knowledgeInfos} 和 {wsxxInfos}（默认模式）'
    )

    parser.add_argument(
        '--standard-mode',
        '--full',
        dest='standard_mode',
        action='store_true',
        help='使用标准模式：生成完整的提示词，包含执法指引和待审查文书占位符'
    )

    return parser.parse_args()


def main():
    """主执行函数，处理命令行参数并调用核心功能。"""
    # 解析命令行参数
    args = parse_arguments()

    # 从命令行参数获取配置
    OUTPUT_FOLDER = args.output
    VERSION = args.version
    USE_EXCEL_GUIDANCE = not args.no_guidance
    # 默认使用占位符模式，除非明确指定使用标准模式
    USE_PLACEHOLDER_MODE = not getattr(args, 'standard_mode', False)
    # 如果用户明确指定了 --placeholder-mode，则强制使用占位符模式
    if args.placeholder_mode:
        USE_PLACEHOLDER_MODE = True

    print("=" * 60)
    print(f"📋 法律审查Prompt生成器 {VERSION}")
    print("=" * 60)

    # 使用命令行参数指定的文件路径
    EXCEL_FILE_PATH = args.file

    print(f"📄 Excel文件: {EXCEL_FILE_PATH}")
    print(f"📁 输出文件夹: {OUTPUT_FOLDER}")
    if USE_PLACEHOLDER_MODE:
        print(f"🔧 生成模式: 占位符模式（只生成审查点，执法指引和待审查文书使用占位符）")
    else:
        print(f"🔧 执法指引: {'使用Excel中的内容' if USE_EXCEL_GUIDANCE else '留空待自定义'}")

    print(f"\n✅ 最终配置:")
    print(f"   版本: {VERSION}")
    if USE_PLACEHOLDER_MODE:
        print(f"   生成模式: 占位符模式（只生成审查点，执法指引和待审查文书使用占位符）")
    else:
        print(f"   执法指引: {'使用Excel中的内容' if USE_EXCEL_GUIDANCE else '留空待自定义'}")
    print()

    # 检查Excel文件是否存在
    if not os.path.exists(EXCEL_FILE_PATH):
        print(f"⚠️  找不到Excel文件: {EXCEL_FILE_PATH}")
        print("请准备好Excel文件后重新运行脚本。")
        return

    # 执行主函数
    generate_prompts_from_excel(EXCEL_FILE_PATH, OUTPUT_FOLDER, VERSION, USE_EXCEL_GUIDANCE, USE_PLACEHOLDER_MODE)

    print("\n" + "=" * 60)
    print("🎉 所有 Prompt 已生成完毕！")
    print(f"📁 请检查输出文件夹: ./{OUTPUT_FOLDER}/version_{VERSION}/")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已被用户中断。")
