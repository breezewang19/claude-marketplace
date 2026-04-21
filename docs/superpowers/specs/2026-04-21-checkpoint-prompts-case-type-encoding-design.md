# Checkpoint-Prompts-Generator: 案件类型分离 + 编码修复

## 背景

当前 checkpoint-prompts-generator 存在两个问题：

1. **刑事/行政混合生成**：用户提供的CSV可能包含行政或刑事案件审查点，但脚本不区分案件类型，导致生成的Prompt和落库CSV中行政/刑事混在一起，落库匹配时出现大量未匹配项（如行政CSV匹配到刑事模板条目）。
2. **Windows编码问题**：subprocess调用Python脚本时stdout/stderr使用系统GBK编码导致乱码；用户提供的CSV文件可能非UTF-8编码导致读取失败。

## 设计

### 1. 案件类型分离

**用户场景**：
- 单文件：只提供行政或刑事CSV，只生成对应类型
- 双文件：同时提供两个文件，分别生成后合并到同一输出目录

**改动项**：

#### 1.1 `legal_review_prompt_generator_v4.0_R.py` 新增 `--case-type` 参数

- 参数值：`xz`（行政）、`xs`（刑事）、`all`（默认，不过滤）
- 读取CSV后按B列（"审查环节-核心文书"列）过滤行：
  - `--case-type xz`：只保留B列包含"行政"的行
  - `--case-type xs`：只保留B列包含"刑事"的行
  - `--case-type all`：不过滤（保持向后兼容）
- 注：A列"审查类别"值为"程序审查"、"证据审查"等，不含案件类型标识；B列"审查环节-核心文书"的值如"行政立案-行政案件立案登记表"、"传唤情况-传唤证"等包含案件类型关键词
- 生成文件名不变（审查环节名已包含区分信息）

#### 1.2 `generate_db_csv.py` 保持不变

已有 `--case-type` 参数和对应的模板加载逻辑，无需修改。

#### 1.3 SKILL.md 流程变更

**Step 2 验证**：
- 支持用户输入1个或2个文件路径（空格或逗号分隔）
- 每个文件独立验证
- 从文件名自动推断案件类型：
  - 文件名含"行政"→ xz
  - 文件名含"刑事"→ xs
  - 无法推断→ 提示用户选择

**Step 3a 确认**：
- 单文件：显示检测到的案件类型
- 双文件：显示两个文件及各自案件类型

**Step 5 执行**：
- 单文件：执行1次，带 `--case-type xz/xs`
- 双文件：执行2次（先行政后刑事），输出到同一 version 目录
- 双文件 Mode B/C：两次执行后合并落库CSV为一个文件

**Step 6a 成功**：
- 显示所有生成文件列表
- 双文件时分别标注案件类型统计

### 2. 编码问题修复

#### 2.1 脚本读取文件：编码自动检测 fallback

两个Python脚本中的 `pd.read_csv()` 调用改为使用 fallback 链：

```python
def read_file_with_fallback(file_path):
    for encoding in ['utf-8-sig', 'utf-8', 'gbk', 'gb18030']:
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法以支持的编码读取文件: {file_path}")
```

- `utf-8-sig`：优先处理带 BOM 的 UTF-8
- `utf-8`：标准 UTF-8
- `gbk`：中文 Windows 常见编码
- `gb18030`：GBK 超集，最终 fallback

#### 2.2 脚本写入文件：统一 UTF-8

保持现有 `encoding='utf-8'` 不变。

#### 2.3 SKILL.md subprocess 调用：设置环境变量

```python
env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', env=env)
```

#### 2.4 验证步骤：报告文件编码

Step 2 验证文件时，检测并报告文件编码，让用户知晓。

## 改动范围

| 文件 | 改动内容 |
|------|----------|
| `legal_review_prompt_generator_v4.0_R.py` | 新增 `--case-type` 参数 + A列过滤逻辑 + 编码 fallback |
| `generate_db_csv.py` | 编码 fallback（已有 `--case-type`） |
| `SKILL.md` | 支持双文件输入 + 案件类型推断 + subprocess 编码设置 + 合并输出逻辑 |

## 不改动的部分

- 模板文件（`data/` 目录）：已有 xs/xz 分离模板，无需修改
- prompts/ 目录下的 md 文件：内容模板不变
- 生成模式（A/B/C）：逻辑不变
- 备份策略：不变
