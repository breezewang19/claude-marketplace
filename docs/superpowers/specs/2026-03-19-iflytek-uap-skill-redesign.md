# iflytek-uap Skill 重新设计方案

**日期：** 2026-03-19
**状态：** 已批准

---

## 背景

当前 `iflytek-uap` skill 为骨架结构，5 个阶段均为 TODO 占位符，无实际执行逻辑。本次重新设计目标：填充完整实现逻辑，并将内置模板与文档驱动两种方式结合。

---

## 文件结构

```
plugins/iflytek-uap/
├── .claude-plugin/
│   └── plugin.json
└── skills/iflytek-uap/
    ├── SKILL.md                        ← 主流程控制
    ├── spring-boot-vue3-templates.md   ← 内置代码模板（新增）
    └── docs/
        └── README.md                   ← 用户文档配置说明
```

**职责划分：**
- `SKILL.md`：流程控制、用户交互、决策逻辑
- `spring-boot-vue3-templates.md`：所有内置代码片段
- `docs/`：用户提供的 UAP 官方文档（不纳入版本控制）

---

## 核心思路：两者结合

| 情况 | 行为 |
|------|------|
| 用户提供了 UAP 文档 | 读取文档，文档驱动生成代码 |
| 用户没有文档 | 使用内置 Spring Boot + Vue3 标准模板 |

启动时先询问用户，再决定走哪条路径。

---

## SKILL.md 流程设计

### 第一阶段：准备

1. 检查 `docs/` 目录是否存在文档文件
2. 询问用户：
   - 有文档 → 读取文档，进入文档驱动模式
   - 没有文档 → 使用内置 Spring Boot + Vue3 模板
3. 若文档缺失且用户选择文档驱动 → 展示 `docs/README.md` 配置说明，终止并等待用户准备

### 第二阶段：分析项目

1. 扫描工作目录：
   - 检测 `pom.xml` → Spring Boot 后端
   - 检测 `package.json` → 前端框架（Vue3/React/Angular）
   - 检测 `tsconfig.json` → TypeScript
2. 展示检测结果，用户确认或手动补充

### 第三阶段：选择集成模式

展示三个选项，**默认推荐模式 B**：

- **模式 A**：纯前端集成
- **模式 B（推荐）**：前后端协同集成（Spring Boot + Vue3）
- **模式 C**：纯后端集成

用户确认模式 B 或主动选择其他模式后继续。

### 第四阶段：选择集成模块

根据所选模式展示对应模块清单，用户勾选需要生成的模块：

**模式 B 模块清单：**

后端：
- Maven 依赖（uap-starter + exclusions）
- application.yml 配置
- CommonController（getUserInfo + logout）

前端：
- UapUser TypeScript 类型
- axios 响应拦截器
- commonApi（getUserInfo + logout）
- Pinia user store
- 路由守卫（beforeEach）
- Header 组件（用户名 + 退出按钮）
- public/config.js

### 第五阶段：逐模块生成

对每个选中的模块：
1. 说明将要生成的内容和写入路径
2. 用户确认
3. 生成代码（内置模板 或 文档驱动）
4. 写入文件

全部完成后输出集成 Checklist 和常见问题提示。

---

## spring-boot-vue3-templates.md 内容规划

提炼自已验证的两个项目（lw-aqsj、lw-tysjgl），包含以下模块：

| 模块 | 来源章节 |
|------|---------|
| Maven 依赖 | UapSkills 2.1 |
| application.yml | UapSkills 2.2 |
| CommonController | UapSkills 2.3 |
| UapUser SDK 字段说明 | UapSkills 2.4 |
| UapUser TypeScript 类型 | UapSkills 3.1 |
| axios 拦截器 | UapSkills 3.2 |
| commonApi | UapSkills 3.3 |
| Pinia user store | UapSkills 3.4 |
| 路由守卫 | UapSkills 3.5 |
| Header 组件 | UapSkills 3.6 |
| config.js | UapSkills 3.7 |
| 集成 Checklist | UapSkills 四 |
| 常见问题 | UapSkills 五 |

---

## 核心行为规范

- **先问后做**：每个模块生成前需用户确认
- **先说明后生成**：生成文件前描述将要写入的内容和路径
- **推荐但不强制**：模式 B 为推荐选项，用户可自由选择
- **文档优先**：有用户文档时优先使用文档中的接口信息
