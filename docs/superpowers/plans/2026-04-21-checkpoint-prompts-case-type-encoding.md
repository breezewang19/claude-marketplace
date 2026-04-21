# Checkpoint-Prompts-Generator: 案件类型分离 + 编码修复 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 checkpoint-prompts-generator 添加案件类型分离生成功能和编码自动检测修复。

**Architecture:** 在现有两个Python脚本中增加 `--case-type` 参数和编码fallback逻辑，更新SKILL.md支持双文件输入和案件类型自动推断。

**Tech Stack:** Python 3.x, pandas, argparse

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `legal_review_prompt_generator_v4.0_R.py` | Prompt生成主脚本，新增 `--case-type` 参数和编码fallback |
| `generate_db_csv.py` | 落库CSV生成脚本，新增编码fallback（已有 `--case-type`） |
| `SKILL.md` | Skill定义文件，更新流程支持双文件输入和案件类型推断 |

---

### Task 1: 为 legal_review_prompt_generator_v4.0_R.py 添加编码fallback函数

**Files:**
- Modify: `legal_review_prompt_generator_v4.0_R.py:267-279`

- [ ] **Step 1: 在文件开头添加编码fallback函数**

在 `import` 语句后、常量定义前（约第25行后）添加以下函数：

```python
def read_file_with_encoding_fallback(file_path):
    """
    使用编码fallback链读取CSV文件。

    尝试顺序：utf-8-sig → utf-8 → gbk → gb18030

    Args:
        file_path: 文件路径

    Returns:
        pandas.DataFrame: 读取的数据

    Raises:
        ValueError: 所有编码尝试失败时
    """
    import pandas as pd

    ext = os.path.splitext(file_path)[1].lower()
    encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb18030']

    for encoding in encodings:
        try:
            if ext == '.csv':
                df = pd.read_csv(file_path, encoding=encoding)
            else:
                # Excel文件不需要编码参数
                df = pd.read_excel(file_path)
            print(f"  (检测到文件编码: {encoding})")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            # 非编码错误直接抛出
            raise e

    raise ValueError(f"无法以支持的编码读取文件: {file_path}。尝试过: {', '.join(encodings)}")
```

- [ ] **Step 2: 修改 generate_prompts_from_excel 函数中的文件读取逻辑**

将第267-279行的文件读取代码：

```python
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
```

替换为：

```python
    # 1. 读取并预处理数据文件（支持Excel和CSV，带编码fallback）
    try:
        df = read_file_with_encoding_fallback(excel_path)
    except FileNotFoundError:
        print(f"错误：找不到文件 '{excel_path}'。请检查路径是否正确。")
        return
    except ValueError as e:
        print(f"错误：{e}")
        return
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        return
```

- [ ] **Step 3: 验证修改**

运行以下命令确认脚本仍能正常工作：

```bash
cd "d:\projects\claude-marketplace"
PYTHONIOENCODING=utf-8 python "C:\Users\yrwang45\.claude\plugins\cache\yrwang45-marketplace\checkpoint-prompts-generator\1.0.0\skills\checkpoint-prompts-generator\legal_review_prompt_generator_v4.0_R.py" -f "temp\行政审查点+审查规则.csv" -o "test_output" -v "test"
```

预期：脚本正常执行，输出包含 `(检测到文件编码: utf-8)` 或其他检测到的编码。

- [ ] **Step 4: 清理测试输出并提交**

```bash
rm -rf "d:\projects\claude-marketplace\test_output"
git add -A
git commit -m "feat(checkpoint-prompts-generator): add encoding fallback for CSV reading"
```

---

### Task 2: 为 legal_review_prompt_generator_v4.0_R.py 添加 --case-type 参数

**Files:**
- Modify: `legal_review_prompt_generator_v4.0_R.py:477-537, 256-313`

- [ ] **Step 1: 在 parse_arguments 函数中添加 --case-type 参数**

在第536行（`--standard-mode` 参数定义后）添加：

```python
    parser.add_argument(
        '--case-type',
        type=str,
        choices=['xs', 'xz', 'all'],
        default='all',
        help='案件类型：xs=刑事, xz=行政, all=全部（默认：all）'
    )
```

- [ ] **Step 2: 修改 generate_prompts_from_excel 函数签名**

将第256行的函数签名：

```python
def generate_prompts_from_excel(excel_path, output_dir, version, use_excel_guidance, use_placeholder_mode=False):
```

修改为：

```python
def generate_prompts_from_excel(excel_path, output_dir, version, use_excel_guidance, use_placeholder_mode=False, case_type='all'):
```

并更新docstring（第258-265行）添加参数说明：

```python
    """
    从Excel文件生成审查Prompt。

    Args:
        excel_path (str): 包含审查数据的Excel文件路径。
        output_dir (str): 存放生成文件的输出目录名。
        version (str): 版本信息，用于命名。
        use_excel_guidance (bool): 是否使用Excel中的执法指引。
        use_placeholder_mode (bool): 是否使用占位符模式。
        case_type (str): 案件类型过滤，'xs'=刑事, 'xz'=行政, 'all'=全部。
    """
```

- [ ] **Step 3: 在 generate_prompts_from_excel 函数中添加案件类型过滤逻辑**

在第308行（`df_processed` 创建后、`if df_processed.empty` 检查前）添加：

```python
    # 按案件类型过滤（基于B列"审查环节"内容）
    if case_type != 'all':
        if case_type == 'xz':
            filter_keyword = '行政'
        elif case_type == 'xs':
            filter_keyword = '刑事'
        else:
            filter_keyword = None

        if filter_keyword:
            original_count = len(df_processed)
            df_processed = df_processed[
                df_processed['审查环节'].astype(str).str.contains(filter_keyword, na=False)
            ].copy()
            filtered_count = len(df_processed)
            print(f"  (案件类型过滤: {filter_keyword}, 原始{original_count}行 → 保留{filtered_count}行)")
```

- [ ] **Step 4: 修改 main 函数传递 case_type 参数**

在第584行，将：

```python
    generate_prompts_from_excel(EXCEL_FILE_PATH, OUTPUT_FOLDER, VERSION, USE_EXCEL_GUIDANCE, USE_PLACEHOLDER_MODE)
```

修改为：

```python
    generate_prompts_from_excel(EXCEL_FILE_PATH, OUTPUT_FOLDER, VERSION, USE_EXCEL_GUIDANCE, USE_PLACEHOLDER_MODE, args.case_type)
```

并在第574行后添加打印案件类型信息：

```python
    if args.case_type != 'all':
        case_label = "刑事" if args.case_type == "xs" else "行政"
        print(f"   案件类型: {case_label} ({args.case_type})")
```

- [ ] **Step 5: 测试 --case-type 参数**

```bash
cd "d:\projects\claude-marketplace"
PYTHONIOENCODING=utf-8 python "C:\Users\yrwang45\.claude\plugins\cache\yrwang45-marketplace\checkpoint-prompts-generator\1.0.0\skills\checkpoint-prompts-generator\legal_review_prompt_generator_v4.0_R.py" -f "temp\行政审查点+审查规则.csv" -o "test_output" -v "test" --case-type xz
```

预期：输出包含 `(案件类型过滤: 行政, 原始X行 → 保留Y行)`，且只生成行政相关的Prompt。

- [ ] **Step 6: 清理并提交**

```bash
rm -rf "d:\projects\claude-marketplace\test_output"
git add -A
git commit -m "feat(checkpoint-prompts-generator): add --case-type parameter for filtering by case type"
```

---

### Task 3: 为 generate_db_csv.py 添加编码fallback

**Files:**
- Modify: `generate_db_csv.py:12767-12779, 12729, 12745`

- [ ] **Step 1: 在文件开头添加编码fallback函数**

在 `import` 语句后（约第27行后）添加：

```python
def read_file_with_encoding_fallback(file_path):
    """
    使用编码fallback链读取CSV文件。

    尝试顺序：utf-8-sig → utf-8 → gbk → gb18030

    Args:
        file_path: 文件路径

    Returns:
        pandas.DataFrame: 读取的数据

    Raises:
        ValueError: 所有编码尝试失败时
    """
    ext = os.path.splitext(file_path)[1].lower()
    encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb18030']

    for encoding in encodings:
        try:
            if ext == '.csv':
                df = pd.read_csv(file_path, encoding=encoding)
            else:
                df = pd.read_excel(file_path)
            print(f"  (检测到文件编码: {encoding})")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise e

    raise ValueError(f"无法以支持的编码读取文件: {file_path}")
```

- [ ] **Step 2: 修改 generate_db_csv 函数中的文件读取逻辑**

将第12767-12779行：

```python
    # 1. 读取数据文件（支持Excel和CSV）
    try:
        ext = os.path.splitext(excel_path)[1].lower()
        if ext == '.csv':
            df = pd.read_csv(excel_path, encoding='utf-8')
        else:
            df = pd.read_excel(excel_path)
    except FileNotFoundError:
        print(f"错误：找不到文件 '{excel_path}'")
        return {"error": "File not found"}
    except Exception as e:
        print(f"读取Excel文件时发生错误: {e}")
        return {"error": str(e)}
```

替换为：

```python
    # 1. 读取数据文件（支持Excel和CSV，带编码fallback）
    try:
        df = read_file_with_encoding_fallback(excel_path)
    except FileNotFoundError:
        print(f"错误：找不到文件 '{excel_path}'")
        return {"error": "File not found"}
    except ValueError as e:
        print(f"错误：{e}")
        return {"error": str(e)}
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        return {"error": str(e)}
```

- [ ] **Step 3: 修改 load_template_data 函数中的文件读取**

将第12729行和第12745行的 `pd.read_csv(..., encoding='utf-8')` 替换为使用fallback函数。

在第12729行前添加读取逻辑：

```python
    if template_path and os.path.exists(template_path):
        try:
            df = read_file_with_encoding_fallback(template_path)
            return df.to_dict('records')
        except Exception as e:
            print(f"警告：读取模板文件失败: {e}")
```

同样修改第12744-12746行：

```python
    if os.path.exists(template_file):
        try:
            df = read_file_with_encoding_fallback(template_file)
            return df.to_dict('records')
        except Exception as e:
            print(f"警告：读取模板文件失败: {e}，使用内置数据")
            return TEMPLATE_DATA.copy()
```

- [ ] **Step 4: 测试编码fallback**

```bash
cd "d:\projects\claude-marketplace"
PYTHONIOENCODING=utf-8 python "C:\Users\yrwang45\.claude\plugins\cache\yrwang45-marketplace\checkpoint-prompts-generator\1.0.0\skills\checkpoint-prompts-generator\generate_db_csv.py" -f "temp\行政审查点+审查规则.csv" -o "test_output" -v "test" --case-type xz
```

预期：脚本正常执行，输出包含编码检测信息。

- [ ] **Step 5: 清理并提交**

```bash
rm -rf "d:\projects\claude-marketplace\test_output"
git add -A
git commit -m "feat(checkpoint-prompts-generator): add encoding fallback to generate_db_csv.py"
```

---

### Task 4: 更新 SKILL.md 支持双文件输入和案件类型推断

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: 更新 Step 1 欢迎消息**

将第24-25行：

```
请提供您的 Excel 或 CSV 文件路径（支持 .xlsx、.xls、.csv 格式）。
您可以直接粘贴文件路径，或拖拽文件到此处。
```

修改为：

```
请提供您的 Excel 或 CSV 文件路径（支持 .xlsx、.xls、.csv 格式）。
您可以：
- 提供单个文件路径
- 同时提供行政和刑事两个文件（用空格或逗号分隔）

示例：
- 单文件：d:\data\行政审查点+审查规则.csv
- 双文件：d:\data\行政审查点.csv d:\data\刑事审查点.csv
```

- [ ] **Step 2: 更新 Step 2 验证逻辑**

在第29-37行的验证表格后添加案件类型推断逻辑说明：

```
## Step 2: Validate File

When the user provides file path(s), perform the following validation checks:

| 检查项 | 验证方法 | 要求 |
|--------|----------|------|
| 文件存在 | `os.path.exists(file_path)` | 必须通过 |
| 文件类型 | 扩展名为 `.xlsx` / `.xls` / `.csv` | 必须通过 |
| 列数 | `len(df.columns) >= 7` | 必须通过 |
| B-G列非空 | `df.iloc[:, 1:7].notna().any().any()` | 必须通过 |
| 数据内容相似度 | 检查B列是否包含"审查"、"环节"等关键词 | 警告性检查 |

**案件类型推断**：
- 从文件名推断：文件名含"行政"→ xz，含"刑事"→ xs
- 无法推断时：提示用户选择

**双文件处理**：
- 如果用户提供两个文件路径，分别验证
- 推断各自的案件类型
```

- [ ] **Step 3: 更新 Step 3a 确认消息**

将第43-55行替换为：

```
## Step 3a: Validation Passed

Display the confirmation message:

**单文件时：**
```
✅ 文件验证通过！

检测到案件类型：{行政/刑事}
正在使用【占位符模式】生成Prompt。

请选择生成模式：
A) 仅生成 .txt Prompt 文件
B) 生成 .txt + 落库 CSV（推荐）
C) 仅生成落库 CSV

请输入选项 (A/B/C)：
```

**双文件时：**
```
✅ 文件验证通过！

文件1：{文件名1} → {案件类型1}
文件2：{文件名2} → {案件类型2}

正在使用【占位符模式】生成Prompt。

请选择生成模式：
A) 仅生成 .txt Prompt 文件
B) 生成 .txt + 落库 CSV（推荐）
C) 仅生成落库 CSV

请输入选项 (A/B/C)：
```
```

- [ ] **Step 4: 更新 Step 5 执行脚本部分**

将第102-128行的代码块替换为：

```python
import subprocess
import os
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(script_dir, "legal_review_prompt_generator_v4.0_R.py")

# 设置环境变量确保UTF-8输出
env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}

def run_generator(excel_path, case_type):
    """执行单个文件的Prompt生成"""
    cmd = [
        "python",
        script_path,
        "-f", excel_path,
        "-o", "generated_prompts",
        "-v", "v4.0_R",
        "--case-type", case_type
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        env=env
    )
    return result

# 单文件执行
result = run_generator(excel_path, case_type)

returncode = result.returncode
stdout = result.stdout
stderr = result.stderr
```

- [ ] **Step 5: 添加双文件执行逻辑**

在 Step 5 后添加 Step 5a：

```
## Step 5a: Execute for Dual Files (Only When Two Files Provided)

When user provided two files, execute the generator twice:

```python
# 双文件执行
results = []
for file_info in files:
    result = run_generator(file_info['path'], file_info['case_type'])
    results.append({
        'file': file_info['path'],
        'case_type': file_info['case_type'],
        'returncode': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr
    })

# 检查所有执行结果
all_success = all(r['returncode'] == 0 for r in results)
```

**双文件 Mode B/C 落库CSV合并**：

```python
# 合并两个落库CSV
import pandas as pd

csv_files = [
    os.path.join(output_dir, f"aj_dzjz_scyd_prompt_pzxx_{timestamp1}.csv"),
    os.path.join(output_dir, f"aj_dzjz_scyd_prompt_pzxx_{timestamp2}.csv")
]

dfs = [pd.read_csv(f, encoding='utf-8') for f in csv_files if os.path.exists(f)]
if len(dfs) == 2:
    merged_df = pd.concat(dfs, ignore_index=True)
    merged_output = os.path.join(output_dir, f"aj_dzjz_scyd_prompt_pzxx_{final_timestamp}.csv")
    merged_df.to_csv(merged_output, index=False, encoding='utf-8')
```
```

- [ ] **Step 6: 更新 Step 5b DB CSV Generator 调用**

将第136-161行替换为：

```python
import subprocess
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
db_csv_script = os.path.join(script_dir, "generate_db_csv.py")

# 设置环境变量确保UTF-8输出
env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}

cmd = [
    "python",
    db_csv_script,
    "-f", excel_path,
    "-o", "generated_prompts",
    "-v", "v4.0_R",
    "--case-type", case_type  # 添加案件类型参数
]

# If Mode C and .txt files already exist from a previous run:
if txt_dir_path:
    cmd.extend(["-t", txt_dir_path])

result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    encoding='utf-8',
    env=env
)
```

- [ ] **Step 7: 更新 Technical Constraints 部分**

在第214-226行后添加：

```
12. **案件类型推断**: 从文件名自动推断，含"行政"→xz，含"刑事"→xs
13. **双文件支持**: 支持同时处理行政和刑事两个文件，输出到同一目录
14. **Subprocess编码**: 调用Python脚本时设置 `PYTHONIOENCODING=utf-8` 环境变量
15. **文件读取编码**: 脚本内部使用编码fallback链：utf-8-sig → utf-8 → gbk → gb18030
```

- [ ] **Step 8: 更新 Error Handling Flow 图**

将第230-254行的流程图更新为：

```
用户输入文件路径（1个或2个）
        ↓
    验证文件
        ↓
    推断案件类型
        ↓
    ┌─── 验证通过 ───┐
    ↓               ↓
  步骤3a         步骤3b
(确认模式)     (显示错误选项)
    ↓               ↓
  选择模式         1/2
  A/B/C            ↓
    ↓             1 → 修复并继续
  单文件？       2 → 中止
    ↓
  ┌─是─┐  ┌─否─┐
  ↓       ↓
执行1次  执行2次
带case-type 分别带case-type
  ↓       ↓
  └───→ 合并输出 ←───┘
        ↓
    ┌─── 成功 ───┐
    ↓           ↓
  success.md  error_diagnosis.md
    ↓
  (Mode B/C: db_csv_success.md)
```

- [ ] **Step 9: 提交SKILL.md更新**

```bash
git add -A
git commit -m "feat(checkpoint-prompts-generator): update SKILL.md for dual-file input and case type inference"
```

---

### Task 5: 集成测试

**Files:**
- Test: 整体流程

- [ ] **Step 1: 测试单文件行政案件生成**

```bash
cd "d:\projects\claude-marketplace"
PYTHONIOENCODING=utf-8 python "C:\Users\yrwang45\.claude\plugins\cache\yrwang45-marketplace\checkpoint-prompts-generator\1.0.0\skills\checkpoint-prompts-generator\legal_review_prompt_generator_v4.0_R.py" -f "temp\行政审查点+审查规则.csv" -o "test_output" -v "test" --case-type xz
```

预期：只生成行政相关的Prompt文件。

- [ ] **Step 2: 测试单文件刑事案件生成**

如果有刑事CSV文件：

```bash
PYTHONIOENCODING=utf-8 python "C:\Users\yrwang45\.claude\plugins\cache\yrwang45-marketplace\checkpoint-prompts-generator\1.0.0\skills\checkpoint-prompts-generator\legal_review_prompt_generator_v4.0_R.py" -f "temp\刑事审查点+审查规则.csv" -o "test_output" -v "test" --case-type xs
```

- [ ] **Step 3: 测试落库CSV生成**

```bash
PYTHONIOENCODING=utf-8 python "C:\Users\yrwang45\.claude\plugins\cache\yrwang45-marketplace\checkpoint-prompts-generator\1.0.0\skills\checkpoint-prompts-generator\generate_db_csv.py" -f "temp\行政审查点+审查规则.csv" -o "test_output" -v "test" --case-type xz
```

预期：只匹配行政模板，不会出现刑事未匹配项。

- [ ] **Step 4: 清理测试输出**

```bash
rm -rf "d:\projects\claude-marketplace\test_output"
```

- [ ] **Step 5: 最终提交**

```bash
git add -A
git commit -m "feat(checkpoint-prompts-generator): complete case type separation and encoding fix"
```

---

## 改动总结

| 文件 | 改动 |
|------|------|
| `legal_review_prompt_generator_v4.0_R.py` | +编码fallback函数, +`--case-type`参数, +B列过滤逻辑 |
| `generate_db_csv.py` | +编码fallback函数, 修改模板加载使用fallback |
| `SKILL.md` | +双文件输入支持, +案件类型推断, +subprocess编码设置, 更新流程图 |
