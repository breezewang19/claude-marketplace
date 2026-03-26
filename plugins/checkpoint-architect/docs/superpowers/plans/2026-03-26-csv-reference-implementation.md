# CSV 文书要素复用实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 SKILL.md 的 Step 4 和 Step 5 中增加 CSV 查表逻辑，让 AI 生成审查步骤和推荐信息点时精确引用系统中已定义的字段。

**Architecture:** 通过修改 SKILL.md 中的 prompt 指令，在 Step 4/5 执行前让 AI 先读取 CSV 并查找对应文书类型的要素字段列表，将结果注入后续 prompt。CSV 查表是 AI 按照描述的逻辑手动解析 CSV 内容，不是可执行代码。

**Tech Stack:** SKILL.md（纯 prompt 文档修改，无代码）

---

## 文件变更概览

| 文件 | 改动 |
|------|------|
| `plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md` | Step 4 和 Step 5 增加 CSV 查表指令 |

**无新增文件，无测试文件**

---

## Task 1: 在 SKILL.md 开头（Step 3.2 之后）增加 CSV 数据引用说明

**文件：** `plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md`（插入点在 Step 3 结尾、Step 4 开头之前，即 line 306-308 附近）

**目的：** 统一定义 CSV 数据的位置和查表逻辑，供 Step 4 和 Step 5 引用。

- [ ] **Step 1: 添加 CSV 查表逻辑说明节**

在 Step 3 结尾添加新节 `### 3.3 CSV Data Reference`，内容如下：

```
### 3.3 CSV Data Reference

When generating checkpoint content, reference the following CSV file to get precise field definitions for each document type.

**CSV File Location:**
```
temp/【行政】功能目录+文书概要+抽取要素+手写体+公章捺印 - 文书要素清单.csv
```

**CSV Structure:**
- Key column for lookup: `文书名称` (document type name, e.g.,《行政处罚决定书》)
- Target column: `文书概要字段名称` (extractable field names for that document)
- One document type may have multiple rows (each row = one field)
- Collect all non-empty `文书概要字段名称` values for the matching `文书名称`

**CSV Lookup Process (for AI to follow):**
1. Identify the document types from `document_types` state
2. For each document type, search CSV rows where `文书名称` matches
3. Collect all `文书概要字段名称` values that are non-empty
4. Deduplicate the list
5. Return: `{document_type: [field1, field2, ...], ...}`

**If document type NOT found in CSV:**
- Output warning: `⚠️ 文书《xxx》暂无系统抽取要素定义，可能需要新建要素抽取配置。当前步骤基于通用逻辑生成。`
- Continue without CSV data, do not block the flow

**If CSV file cannot be read:**
- Same handling as above

**Important:** CSV fields are RECOMMENDED references for AI precision, NOT the only answer. AI should intelligently reference these fields when generating review logic, but still apply judgment to fit the specific review scenario. Avoid over-fitting by mechanically copying every CSV field without context.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md
git commit -m "feat(checkpoint-architect): add CSV data reference section before Step 4"
```

---

## Task 2: 修改 Step 4 Quick Mode (A) prompt，增加 CSV 查表指令

**文件：** `plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md:316-338`（Step 4A Processing Instructions 部分）

**改动点：** 在现有的 "Processing Instructions" 开头增加 CSV 查表步骤，将字段列表注入 prompt。

**改动前（lines 322-338）：**
```
**Processing Instructions:**
1. Parse the user's natural language description
2. Identify key steps, conditions, and decision points
3. Transform into structured steps using the format:
   - 第一步：[step description]
   - 第二步：[step description]
   - 第三步：得出结论
4. Ensure all required elements are included:
   - Document existence check with "若缺少以上文书，则判定为'缺少文书材料'"
   - Clear judgment statements using "判定为'存在问题'" / "判定为'不存在问题'" / "判定为'缺少文书材料'"
   - Document names in 《》 format
5. Use professional legal terminology
6. **Infer information points** using the hybrid method:
   - **Keyword matching**: Extract keywords (时间、时长、期限、编号、签名、盖章、审批、金额、状态等) from the description
   - **Logic inversion**: Infer required data points from decision conditions (e.g., "超过12小时" implies need for duration/time data)
   - Group inferred points by document type using 「」 format
   - Only include points that can be inferred; do not fabricate
```

**改动后：**
```
**Processing Instructions:**
0. **CSV Lookup (for each document type):**
   - Reference the CSV data as described in section 3.3
   - Get the list of extractable fields for each document in `document_types`
   - If CSV data found: note the fields for use in steps 2 and 6
   - If NOT found: output warning per section 3.3

1. Parse the user's natural language description
2. Identify key steps, conditions, and decision points
3. Transform into structured steps using the format:
   - 第一步：[step description]
   - 第二步：[step description]
   - 第三步：得出结论
4. Ensure all required elements are included:
   - Document existence check with "若缺少以上文书，则判定为'缺少文书材料'"
   - Clear judgment statements using "判定为'存在问题'" / "判定为'不存在问题'" / "判定为'缺少文书材料'"
   - Document names in 《》 format
5. Use professional legal terminology
6. **Reference CSV fields for precision:**
   - When describing conditions that check specific field values, reference the CSV field names exactly (e.g., "检查《处罚结论》字段是否为'罚款'" instead of vague "检查处罚结论")
   - Use CSV fields as guidance for what information is extractable from each document
   - Still apply judgment to select relevant fields for the specific review logic — do not mechanically include every CSV field
```

- [ ] **Step 1: Apply the edit above**（使用 Edit 工具，old_string 为改动前内容，new_string 为改动后内容）

- [ ] **Step 2: Commit**

```bash
git add plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md
git commit -m "feat(checkpoint-architect): inject CSV field lookup into Step 4A prompt"
```

---

## Task 3: 修改 Step 4 Guided Mode (B) prompt，增加 CSV 查表指令

**文件：** `plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md:354-365`（Step 4B Processing Instructions 部分）

**改动点：** 在 Guided Mode 的 "Processing Instructions" 开头同样增加 CSV 查表。

**改动前（lines 354-365）：**
```
**Processing Instructions:**
1. Wait for the user's pattern selection
2. Retrieve the corresponding template from checkpoint-templates.md
3. Present the guided questions from the template ONE AT A TIME
4. Apply persistent questioning logic to ensure complete answers
5. Generate structured content using the template's step structure
6. Fill in placeholders with user's specific information
7. **Infer information points** using the hybrid method:
   - **Keyword matching**: Extract keywords (时间、时长、期限、编号、签名、盖章、审批、金额、状态等) from the user's answers
   - **Logic inversion**: Infer required data points from decision conditions in the template
   - Group inferred points by document type using 「」 format
   - Only include points that can be inferred; do not fabricate
```

**改动后：**
```
**Processing Instructions:**
0. **CSV Lookup (for each document type):**
   - Reference the CSV data as described in section 3.3
   - Get the list of extractable fields for each document in `document_types`
   - If CSV data found: note the fields for use in steps 5 and 7
   - If NOT found: output warning per section 3.3

1. Wait for the user's pattern selection
2. Retrieve the corresponding template from checkpoint-templates.md
3. Present the guided questions from the template ONE AT A TIME
4. Apply persistent questioning logic to ensure complete answers
5. Generate structured content using the template's step structure
6. Fill in placeholders with user's specific information
7. **Reference CSV fields for precision:**
   - When describing conditions that check specific field values, reference the CSV field names exactly
   - Use CSV fields as guidance for what information is extractable from each document
   - Still apply judgment to select relevant fields for the specific review logic — do not mechanically include every CSV field
```

- [ ] **Step 1: Apply the edit above**

- [ ] **Step 2: Commit**

```bash
git add plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md
git commit -m "feat(checkpoint-architect): inject CSV field lookup into Step 4B prompt"
```

---

## Task 4: 修改 Step 5 Output Template 中的 information points 格式说明

**文件：** `plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md:1036-1050`（Step 6.1 Output Template 的 Information Points Format 部分）

**目的：** 明确 Step 5 输出信息点时优先使用 CSV 数据，替代 keyword matching。

**改动前（lines 1036-1050）：**
```
**Information Points Format:**

The inferred_information_points should be formatted as:

```
从《文书名称1》抽取：
- 「信息点1」
- 「信息点2」

从《文书名称2》抽取：
- 「信息点3」
- 「信息点4」
```

Group by document type, use 「」 brackets for each point, and only include points that can be inferred from the review logic.
```

**改动后：**
```
**Information Points Format:**

优先使用 CSV 中定义的字段名作为信息点。若 CSV 中无该文书数据，则回退到从审查步骤中推断。

优先格式（使用 CSV 字段）：
```
从《文书名称1》抽取：
- 「字段1」
- 「字段2」

从《文书名称2》抽取：
- 「字段3」
- 「字段4」
```

回退格式（无 CSV 数据时）：
```
从《文书名称1》抽取：
- 「从审查步骤推断的信息点1」
- 「从审查步骤推断的信息点2」
```

Group by document type, use 「」 brackets for each point. Prefer CSV field names when available; only infer additional points when CSV data is insufficient.
```

- [ ] **Step 1: Apply the edit above**

- [ ] **Step 2: Commit**

```bash
git add plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md
git commit -m "feat(checkpoint-architect): update Step 5 information points format to prefer CSV fields"
```

---

## Task 5: 在 Step 4 和 Step 5 之间增加 CSV 字段注入说明（可选增强）

**文件：** `plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md` Step 4 结尾到 Step 5 之间的过渡部分

如果 Step 4 和 Step 5 之间有明确的衔接 prompt，在那里增加：
- 明确告知 AI 已在 Step 4 获取到的 CSV 字段列表
- 指示 Step 5 直接使用该列表生成推荐信息点

（此任务为可选，若找不到明确插入点可跳过）

---

## 改动汇总

| Task | 描述 | 改动位置 |
|------|------|----------|
| 1 | 增加 CSV 数据引用说明节 | Step 3 之后 |
| 2 | Step 4A prompt 注入 CSV 查表 | Step 4A Processing Instructions |
| 3 | Step 4B prompt 注入 CSV 查表 | Step 4B Processing Instructions |
| 4 | Step 5 information points 格式更新 | Step 6.1 Output Template |
| 5 | （可选）Step 4/5 衔接处增强 | 过渡 prompt |
