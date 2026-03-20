# Checkpoint Architect - Batch Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Batch Mode (C) to checkpoint-architect skill, allowing automatic batch processing of .md draft files in a directory.

**Architecture:** Single-file modification to `SKILL.md`. All changes are insertions — existing content (Steps 1-2, A/B mode logic, Steps 5-9) is preserved. Batch mode hooks into the existing generation pipeline (Step 4 quick-mode path, Step 5, Step 7, Step 8) without duplicating that logic.

**Tech Stack:** Skill file only (SKILL.md), no code dependencies.

---

## File Structure

**Modify:** `plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md`

Three insertion points in a ~1427-line file:
1. **Step 3** (lines 284-300): Add option C to mode selection
2. **After Step 4B** (after line 616, before "## Step 5"): Add new section "### If User Selects Batch Mode (C)"
3. **Step 9** (lines 1332-1347): Extend success message to show batch mode summary report

---

## Task 1: Add Option C to Step 3 Mode Selection

**File:** `plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md:284-300`

- [ ] **Step 1: Add option C block after option B**

Find this text (lines 293-297):
```
**B. 引导模式（Guided Mode）**
- 适合：不确定如何组织审查逻辑，需要逐步引导
- 方式：我会根据常见审查模式提供模板和引导问题
- 优点：结构清晰，适合新手用户

**请选择模式：A 或 B**
```

Replace with:
```
**B. 引导模式（Guided Mode）**
- 适合：不确定如何组织审查逻辑，需要逐步引导
- 方式：我会根据常见审查模式提供模板和引导问题
- 优点：结构清晰，适合新手用户

**C. 批量模式（Batch Mode）**
- 适合：已有一批逻辑基本清晰的审查点草稿文件
- 方式：指定目录，AI 自动解析并批量生成，无需交互
- 💡 提示：批量模式适合快速处理大量草稿，但 AI 自动解析可能存在偏差。
         若对准确性要求较高，建议使用快速模式（A）或引导模式（B）逐一处理。

**请选择模式：A、B 或 C**
```

- [ ] **Step 2: Commit**

```bash
git add plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md
git commit -m "feat(checkpoint-architect): add batch mode option C to step 3"
```

---

## Task 2: Add Step 4C — Batch Mode Processing Logic

**File:** `plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md:616` (after line 616, before "## Step 5")

- [ ] **Step 1: Verify insertion point**

Confirm that line 616 ends with "Proceed to Step 5 (Generate Logic Diagram)." and line 617 is "## Step 5: Generate Logic Diagram".

- [ ] **Step 2: Insert Step 4C section**

Insert the following new section between the Guided Mode content and "## Step 5":

```
### If User Selects Batch Mode (C)

Batch mode processes all .md draft files in a user-specified directory automatically.

#### 4C.1 Collect Directory Path

Prompt the user:

```
请提供包含审查点草稿文件的目录路径：

例如：/mnt/d/projects/TOY/CheckPoints/input

注意：
- 仅处理当前目录下的 .md 文件（不递归子目录）
- 目录需存在且包含至少一个 .md 文件
```
```

#### 4C.2 Validate and Scan Directory

After receiving the path:

1. **Validate path exists**: If path does not exist or is not a directory, display:
   ```
   ❌ 路径不存在或不是有效目录，请检查后重新输入。
   ```
   Then ask for path again.

2. **Scan for .md files**: List all `.md` files in the directory (non-recursive).
   - If no `.md` files found, display:
     ```
     ❌ 该目录下未找到任何 .md 文件。
     请确认目录路径是否正确，或将草稿文件放入该目录后重试。
     ```
     Then exit batch mode (return to Step 3).

3. **Display found files and request confirmation**:
   ```
   📁 发现 {N} 个审查点草稿文件：

   1. 文件名A.md
   2. 文件名B.md
   ...

   是否开始批量处理？（输入"是"开始，输入其他取消）
   ```

#### 4C.3 Batch Processing Loop

For each `.md` file in the directory, process sequentially:

**For each file:**

1. **Parse file content**
   - Read the file content
   - Extract `checkpoint_name`:
     - Look for phrases containing: 是否、有无、合规、检查
     - Fallback: first line of file or filename (strip `.md` suffix)
     - Validate: 5-50 Chinese characters, non-empty
   - Extract `document_types`:
     - Find content in 《》 brackets
     - Find words with: 证、书、表、单、函、通知
     - Validate: at least one document type found
   - Extract review logic:
     - Identify steps, conditions, and conclusions from the text
     - Convert to structured format (第一步/第二步/第三步)

2. **Parse failure handling**
   If any parse success condition fails:
   - Record failure with reason: "无法识别审查点名称" / "无法识别文书类型" / "内容为空或无意义"
   - Skip to next file (do not generate output)
   - Continue processing remaining files

3. **Execute generation pipeline** (on successful parse)
   - Write extracted `checkpoint_name` and `document_types` to internal state
   - **Apply Step 4A processing instructions** (SKILL.md lines 316-332):
     - The parsed file content (审查逻辑 text) is treated as if the user had typed it in Quick Mode
     - Skip the user prompt "请用自然语言描述审查逻辑：" and example display
     - Apply all Processing Instructions (keyword matching, logic inversion, information points inference) using the parsed logic text as input
   - Execute Step 5 (generate Mermaid + ASCII diagrams)
   - Skip Step 6 (no interactive review in batch mode)
   - Execute Step 7 (validation)
     - If validation passes → continue to Step 8
     - If validation fails → attempt auto-fix once; if still failing, mark as failed and skip
   - Execute Step 8 (write output file)
     - Output path: `/mnt/d/projects/TOY/CheckPoints/output/`
     - Filename: `YYYY-MM-DD-{checkpoint_name}.md`
     - If file already exists, append `-2`, `-3`, etc. to the checkpoint_name portion:
       Example: `2026-03-20-传唤时长是否合规-2.md`

4. **Track results**
   Maintain a running tally:
   - `batch_success_count`
   - `batch_failure_count`
   - `batch_success_list` (output file paths)
   - `batch_failure_list` (input file paths + reasons)

#### 4C.4 Display Batch Summary Report

After all files are processed, display:

```
批量处理完成
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 成功：{N} 个
❌ 失败：{M} 个（已跳过）

【成功列表】
- /mnt/d/projects/TOY/CheckPoints/output/2026-03-20-审查点名称A.md
- /mnt/d/projects/TOY/CheckPoints/output/2026-03-20-审查点名称B.md

【失败列表】
- /path/to/input/文件名.md - 原因：无法识别审查点名称

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 对于失败的文件，建议使用快速模式（A）或引导模式（B）手动处理。
```

- [ ] **Step 3: Commit**

```bash
git add plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md
git commit -m "feat(checkpoint-architect): implement batch mode step 4C processing logic"
```

---

## Task 3: Update Step 9 Success Message

**File:** `plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md` (insertion point after line 1347)

The existing Step 9 success message is for single checkpoint creation. In batch mode, the summary report is shown during Step 4C processing (4C.4), not here. No changes needed to Step 9 — it correctly serves single-checkpoint A/B mode.

However, add a note clarifying this behavior.

- [ ] **Step 1: Find Step 9 section**

Find (lines 1332-1347):
```
## Step 9: Success Message

Display the completion message:

```
✅ 审查点创建成功！

文件已保存至：output/{filename}

你可以：
1. 将此内容复制到Excel中，由Python程序进一步处理
2. 继续创建下一个审查点
3. 查看生成的文件内容
```

Ask the user if they want to create another checkpoint or exit.
```

- [ ] **Step 2: Add clarifying note**

After "Ask the user if they want to create another checkpoint or exit." add:

```
**Note:** When running in Batch Mode (C), the summary report is displayed during Step 4C processing (section 4C.4), not here. Step 9 is only reached for single-checkpoint creation via Mode A or B.
```

- [ ] **Step 3: Commit**

```bash
git add plugins/checkpoint-architect/skills/checkpoint-architect/SKILL.md
git commit -m "docs(checkpoint-architect): clarify step 9 is for single mode only"
```

---

## Summary

| Task | Change | Lines |
|------|--------|-------|
| 1 | Add option C to Step 3 | ~293-300 |
| 2 | Add Step 4C batch mode logic | After ~616 |
| 3 | Add note to Step 9 | After ~1347 |
