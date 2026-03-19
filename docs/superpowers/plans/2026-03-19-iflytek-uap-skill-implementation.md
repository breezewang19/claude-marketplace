# iflytek-uap Skill 实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 iflytek-uap skill 从骨架结构升级为可执行的完整 skill，支持内置 Spring Boot + Vue3 模板和文档驱动两种模式。

**Architecture:** SKILL.md 负责流程控制和用户交互，spring-boot-vue3-templates.md 存放所有内置代码模板。启动时先询问用户选择代码生成方式（内置模板 or 文档驱动），若选文档驱动但 docs/ 为空则终止并提示配置。第三阶段默认推荐模式 B（前后端协同）。内置模板和文档驱动是平等的两条路径，由用户主动选择。

**Tech Stack:** Claude skill（Markdown 指令文件）、Spring Boot、Vue3、TypeScript、Pinia、axios

---

## 文件清单

| 操作 | 文件 | 职责 |
|------|------|------|
| 修改 | `plugins/iflytek-uap/skills/iflytek-uap/SKILL.md` | 主流程控制，替换 TODO 为完整指令 |
| 新建 | `plugins/iflytek-uap/skills/iflytek-uap/spring-boot-vue3-templates.md` | 内置代码模板 |
| 保持 | `plugins/iflytek-uap/skills/iflytek-uap/docs/README.md` | 用户文档配置说明，无需修改 |
| 保持 | `plugins/iflytek-uap/.claude-plugin/plugin.json` | 元数据，无需修改 |

---

## Task 1：创建 spring-boot-vue3-templates.md

**Files:**
- Create: `plugins/iflytek-uap/skills/iflytek-uap/spring-boot-vue3-templates.md`
- Source: `TEMP/UapSkills.md`（内容来源，不提交到 git，仅作为编写参考）

> 注意：`TEMP/UapSkills.md` 是本地参考文件，内容需直接写入模板文件，不依赖运行时读取。

- [ ] **Step 1：写入文件头部和后端模板（Maven 依赖 + application.yml）**

读取 `TEMP/UapSkills.md` 第 2.1 节（Maven 依赖）和 2.2 节（application.yml），将完整代码写入新文件：

```
plugins/iflytek-uap/skills/iflytek-uap/spring-boot-vue3-templates.md
```

文件结构：
```markdown
# Spring Boot + Vue3 内置模板

> 提炼自已验证项目（lw-aqsj、lw-tysjgl），适用于 Spring Boot + Vue3 前后端分离项目。

---

## 后端模板

### 模板 B1：Maven 依赖
（完整 pom.xml 片段，含三个 exclusion）

### 模板 B2：application.yml 配置
（完整 uap.* 配置项，含占位符说明）
```

验收标准：文件存在，包含完整 xml 和 yaml 代码块，无截断。

- [ ] **Step 2：追加 CommonController 和 SDK 说明**

读取 `TEMP/UapSkills.md` 2.3（CommonController 完整 Java 代码）和 2.4（SDK API 速查表 + UapUser 字段列表），追加到模板文件。

验收标准：包含完整 Java 类代码和 Markdown 表格。

- [ ] **Step 3：追加前端模板（UapUser 类型 + axios 拦截器 + commonApi）**

读取 `TEMP/UapSkills.md` 3.1、3.2、3.3，追加到模板文件。

验收标准：包含完整 TypeScript 接口定义、axios 拦截器代码、API 函数定义。

- [ ] **Step 4：追加前端模板（Pinia store + 路由守卫 + Header 组件 + config.js）**

读取 `TEMP/UapSkills.md` 3.4、3.5、3.6、3.7，追加到模板文件。

验收标准：包含完整 Pinia store、router guard、Vue 组件、config.js 代码。

- [ ] **Step 5：追加集成 Checklist 和常见问题**

读取 `TEMP/UapSkills.md` 第四节（Checklist）和第五节（常见问题），追加到模板文件。

验收标准：包含后端和前端两个 Checklist，以及至少 5 条常见问题。

- [ ] **Step 6：提交**

```bash
git add plugins/iflytek-uap/skills/iflytek-uap/spring-boot-vue3-templates.md
git commit -m "feat(iflytek-uap): add spring-boot-vue3 built-in templates"
```

---

## Task 2：重写 SKILL.md — 第一阶段（准备）

**Files:**
- Modify: `plugins/iflytek-uap/skills/iflytek-uap/SKILL.md`

- [ ] **Step 1：替换文件头部和概述**

保留 frontmatter，将 `# Claude 操作指南` 和概述部分更新为完整说明，包含两种模式的说明。

验收标准：概述部分包含以下内容：
- UAP CAS 核心流程（5 步）
- 两种代码生成方式说明（内置模板 vs 文档驱动）
- 核心行为规范（先问后做、先说明后生成、推荐但不强制）

- [ ] **Step 2：实现第一阶段：准备**

替换第一阶段 TODO，写入以下逻辑：

```markdown
## 第一阶段：准备

### 1.1 询问用户选择代码生成方式

使用 AskUserQuestion 工具询问：

**问题：** 请选择代码生成方式
- **选项 A：使用内置模板**（Spring Boot + Vue3 标准方案，无需额外文档，直接生成）
- **选项 B：使用 UAP 文档驱动**（根据你提供的 UAP 官方文档生成，适配任意版本）

### 1.2 处理文档驱动路径

若用户选择 B：
- 使用 Glob 检查 `{skill_dir}/docs/` 目录是否存在 `uap-quick-reference.md` 或 PDF 文件
- 若 docs/ 有文档 → 读取文档，记录模式为"文档驱动"，进入第二阶段
- 若 docs/ 为空 → 展示 docs/README.md 内容，提示用户先放置文档后重新运行 skill，**终止执行**

### 1.3 处理内置模板路径

若用户选择 A：
- 记录模式为"内置模板"，直接进入第二阶段
```

验收标准：
- 第一阶段先询问用户，不自动检测
- 文档驱动路径：有文档继续，无文档终止
- 内置模板路径：直接继续

- [ ] **Step 3：提交**

```bash
git add plugins/iflytek-uap/skills/iflytek-uap/SKILL.md
git commit -m "feat(iflytek-uap): implement phase 1 - preparation"
```

---

## Task 3：重写 SKILL.md — 第二阶段（分析项目）

**Files:**
- Modify: `plugins/iflytek-uap/skills/iflytek-uap/SKILL.md`

- [ ] **Step 1：实现第二阶段：分析项目**

替换第二阶段 TODO，写入以下逻辑：

```markdown
## 第二阶段：分析项目

### 2.1 扫描项目结构

使用 Glob 工具检测：
- `**/pom.xml` → 存在则标记后端为 Spring Boot
- `**/package.json` → 读取 dependencies 检测前端框架
  - 包含 `vue` → Vue3
  - 包含 `react` → React
  - 包含 `@angular/core` → Angular
- `**/tsconfig.json` → 存在则标记语言为 TypeScript

### 2.2 展示检测结果并确认

向用户展示检测结果：
- 后端：Spring Boot / 未检测到
- 前端：Vue3 / React / Angular / 未检测到
- 语言：TypeScript / JavaScript

使用 AskUserQuestion 询问：
- **正确，继续** → 进入第三阶段
- **需要修改** → 询问用户手动输入技术栈，更新后继续
```

- [ ] **Step 2：提交**

```bash
git add plugins/iflytek-uap/skills/iflytek-uap/SKILL.md
git commit -m "feat(iflytek-uap): implement phase 2 - project analysis"
```

---

## Task 4：重写 SKILL.md — 第三阶段（选择集成模式）

**Files:**
- Modify: `plugins/iflytek-uap/skills/iflytek-uap/SKILL.md`

- [ ] **Step 1：实现第三阶段：选择集成模式**

替换第三阶段 TODO，写入以下逻辑：

```markdown
## 第三阶段：选择集成模式

使用 AskUserQuestion 工具展示三个选项，**明确标注推荐模式 B**：

**问题：** 请选择集成模式

- **模式 A**：纯前端集成 — 前端直接调用 UAP 接口，适合无后端或后端不需要验证身份的场景
- **模式 B（推荐）**：前后端协同集成（Spring Boot + Vue3）— 后端 uap-starter 接管认证，前端处理跳转，适合标准前后端分离项目
- **模式 C**：纯后端集成 — 后端处理全部认证逻辑，适合传统 MPA 应用

若用户选择 B 或未明确表示其他选项 → 使用模式 B 继续。
若用户明确选择 A 或 C → 记录模式，进入第四阶段（展示对应模块清单）。
```

- [ ] **Step 2：提交**

```bash
git add plugins/iflytek-uap/skills/iflytek-uap/SKILL.md
git commit -m "feat(iflytek-uap): implement phase 3 - mode selection with B recommended"
```

---

## Task 5：重写 SKILL.md — 第四阶段（选择模块）

**Files:**
- Modify: `plugins/iflytek-uap/skills/iflytek-uap/SKILL.md`

- [ ] **Step 1：实现第四阶段：选择集成模块**

替换第四阶段 TODO，写入模式 B 的完整模块清单：

```markdown
## 第四阶段：选择集成模块

根据所选模式展示模块清单，使用 AskUserQuestion（multiSelect: true）让用户勾选。

### 模式 B 模块清单

**后端模块：**
- [ ] Maven 依赖（uap-starter + 三个 exclusion）
- [ ] application.yml 配置（uap.* 配置项）
- [ ] CommonController（getUserInfo + logout 接口）

**前端模块：**
- [ ] UapUser TypeScript 类型定义
- [ ] axios 响应拦截器（处理 ret=302 跳转）
- [ ] commonApi（getUserInfo + logout）
- [ ] Pinia user store
- [ ] 路由守卫（beforeEach 自动获取用户信息）
- [ ] Header 组件（用户名展示 + 退出按钮）
- [ ] public/config.js（后端地址注入）

默认全选，用户可取消不需要的模块。
```

- [ ] **Step 2：追加模式 A 和模式 C 的模块清单**

模式 A（纯前端）模块清单：
- UapUser TypeScript 类型定义
- axios 响应拦截器（处理 ret=302）
- commonApi（getUserInfo + logout）
- Pinia user store
- 路由守卫
- Header 组件
- public/config.js

模式 C（纯后端）模块清单：
- Maven 依赖
- application.yml 配置
- CommonController（getUserInfo + logout）

验收标准：三种模式均有独立的模块清单，multiSelect 选项与模式对应。

- [ ] **Step 3：提交**

```bash
git add plugins/iflytek-uap/skills/iflytek-uap/SKILL.md
git commit -m "feat(iflytek-uap): implement phase 4 - module selection"
```

---

## Task 6：重写 SKILL.md — 第五阶段（生成代码）

**Files:**
- Modify: `plugins/iflytek-uap/skills/iflytek-uap/SKILL.md`

- [ ] **Step 1：实现第五阶段：逐模块生成**

替换第五阶段 TODO，写入生成逻辑：

```markdown
## 第五阶段：逐模块生成

对每个用户选中的模块，按以下步骤执行：

### 5.1 说明阶段

向用户说明：
- 将要生成的文件路径（如 `src/main/java/.../CommonController.java`）
- 文件的作用
- 若文件已存在，说明将要修改的内容

### 5.2 确认阶段

使用 AskUserQuestion 询问：
- **生成** → 继续
- **跳过** → 跳过此模块
- **修改路径** → 询问用户输入目标路径

### 5.3 生成阶段

**内置模板模式：**
读取 `spring-boot-vue3-templates.md` 中对应模板，替换占位符（包名、模块名等），写入目标文件。

**文档驱动模式：**
读取 `docs/` 中的 UAP 文档，提取对应接口信息，生成适配当前技术栈的代码。

### 5.4 完成阶段

所有模块生成完毕后：
1. 展示集成 Checklist（来自 spring-boot-vue3-templates.md）
2. 展示常见问题（来自 spring-boot-vue3-templates.md）
3. 提示用户配置环境变量
```

- [ ] **Step 2：提交**

```bash
git add plugins/iflytek-uap/skills/iflytek-uap/SKILL.md
git commit -m "feat(iflytek-uap): implement phase 5 - code generation"
```

---

## Task 7：验证和收尾

- [ ] **Step 1：检查 SKILL.md 完整性**

使用 Read 工具读取 `plugins/iflytek-uap/skills/iflytek-uap/SKILL.md`，逐项确认：

| 检查项 | 验收标准 |
|--------|---------|
| TODO 残留 | 全文搜索 `TODO`，结果为零 |
| 第一阶段 | 包含 Glob 检查 docs/ 和 AskUserQuestion 两个步骤 |
| 第二阶段 | 包含 Glob 检测 pom.xml/package.json 和确认步骤 |
| 第三阶段 | 包含三个模式选项，模式 B 标注"推荐" |
| 第四阶段 | 包含模式 A/B/C 三套模块清单，模式 B 有 10 个模块（3 后端 + 7 前端） |
| 第五阶段 | 包含说明→确认→生成→写入四步逻辑 |
| 两条路径 | 内置模板和文档驱动均有明确说明 |

- [ ] **Step 2：检查 spring-boot-vue3-templates.md 完整性**

使用 Read 工具读取模板文件，确认以下 13 个模块均存在且代码完整（无 `...` 省略号截断）：

1. Maven 依赖（含三个 exclusion）
2. application.yml（含所有 uap.* 配置项）
3. CommonController（完整 Java 类，含 import）
4. UapUser SDK 字段说明（Markdown 表格）
5. UapUser TypeScript 类型（完整 interface）
6. axios 拦截器（含 ret=302 和 HTTP 302 两种处理）
7. commonApi（getUserInfo + logout）
8. Pinia user store（完整 defineStore）
9. 路由守卫（beforeEach 完整逻辑）
10. Header 组件（完整 Vue SFC）
11. config.js（window.APP_CONFIG）
12. 集成 Checklist（后端 + 前端两个清单）
13. 常见问题（Q1-Q5 全部）

- [ ] **Step 3：最终提交**

```bash
git add plugins/iflytek-uap/
git commit -m "feat(iflytek-uap): complete skill implementation"
```
