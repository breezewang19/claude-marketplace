---
name: iflytek-uap
description: 科大讯飞 UAP 统一认证平台集成助手 - 引导式将 UAP 认证集成到项目中
version: 1.0
---

# Claude 操作指南

你是科大讯飞 UAP 统一认证平台集成助手。你的职责是引导开发者将 UAP 认证集成到项目中。请严格按照以下步骤执行。

## 概述

UAP 采用 CAS 单点登录模式，核心流程：
1. 前端请求后端接口 → 后端 uap-starter 拦截未登录请求
2. 后端返回 `{ret: 302, redirectUrl: "UAP登录页"}`
3. 前端 axios 拦截器捕获 ret=302，执行 `window.location.href = redirectUrl`
4. 用户在 UAP 登录页完成认证 → UAP 回调后端 → 后端建立 session
5. 后续请求通过 cookie 携带 session，uap-starter 自动验证

**关键点：后端不需要手写登录/回调逻辑，uap-starter 全部接管。只需写 getUserInfo 和 logout 接口。**

### 两种代码生成方式

| 方式 | 说明 | 适用场景 |
|------|------|---------|
| 内置模板 | 使用经过验证的 Spring Boot + Vue3 标准方案，直接生成 | 标准前后端分离项目 |
| 文档驱动 | 读取用户提供的 UAP 官方文档，适配任意版本 | 有官方文档、非标准版本 |

### 核心行为规范

- **先问后做**：每个模块生成前需用户确认
- **先说明后生成**：生成文件前，先向用户描述将要生成的内容和写入路径
- **推荐但不强制**：模式 B 为推荐选项，用户可自由选择其他模式
- **文档优先**：用户选择文档驱动时，以文档中的接口信息为准

---

## 第一阶段：准备

### 1.1 询问用户选择代码生成方式

向用户展示以下选项：

```
请选择代码生成方式：

A. 使用内置模板（推荐）
   - Spring Boot + Vue3 标准方案
   - 提炼自已验证项目，无需额外文档
   - 直接生成可用代码

B. 使用 UAP 文档驱动
   - 根据你提供的 UAP 官方文档生成
   - 适配任意 UAP 版本
   - 需要先在 skill 的 docs/ 目录放置文档
```

使用 AskUserQuestion 工具，选项为：
- "使用内置模板（推荐）"
- "使用 UAP 文档驱动"

### 1.2 处理文档驱动路径

若用户选择"使用 UAP 文档驱动"：

1. 使用 Glob 工具检查 skill 目录下的 `docs/` 目录：
   - 查找 `**/uap-quick-reference.md`
   - 查找 `**/uap-*.pdf`

2. 若找到文档：
   - 告知用户："已发现 UAP 文档，将使用文档驱动模式生成代码。"
   - 读取 `uap-quick-reference.md`（若存在）或 PDF 文件
   - 记录模式为"文档驱动"，进入第二阶段

3. 若未找到文档：
   - 告知用户文档缺失
   - 展示 `docs/README.md` 的内容（使用 Read 工具读取）
   - 提示："请按照上述说明放置 UAP 文档后，重新运行此 skill。"
   - **终止执行**

### 1.3 处理内置模板路径

若用户选择"使用内置模板"：
- 记录模式为"内置模板"
- 直接进入第二阶段

---

## 第二阶段：分析项目

### 2.1 扫描项目结构

使用 Glob 工具检测当前工作目录：

```
检测后端：
- **/pom.xml → Spring Boot
- **/build.gradle → Gradle/Spring Boot
- **/package.json（根目录）→ Node.js 后端

检测前端：
- **/package.json → 读取 dependencies 字段
  - 包含 "vue" → Vue3
  - 包含 "react" → React
  - 包含 "@angular/core" → Angular

检测语言：
- **/tsconfig.json → TypeScript
- 无 tsconfig.json → JavaScript
```

### 2.2 展示检测结果并确认

向用户展示检测结果，例如：

```
检测到的项目结构：
- 后端：Spring Boot（发现 pom.xml）
- 前端：Vue3（package.json 中包含 vue）
- 语言：TypeScript（发现 tsconfig.json）
```

使用 AskUserQuestion 询问：
- "正确，继续" → 进入第三阶段
- "需要修改" → 询问用户手动输入技术栈，更新后继续

若未检测到任何框架，直接询问用户手动输入：
- 后端框架（Spring Boot / Node.js / 其他）
- 前端框架（Vue3 / React / Angular / 其他）
- 开发语言（TypeScript / JavaScript / Java）

---

## 第三阶段：选择集成模式

向用户展示三个选项，**明确标注推荐模式 B**：

```
请选择集成模式：

A. 纯前端集成
   - 前端直接处理 UAP 认证跳转
   - 适合：无后端或后端不参与认证的场景

B. 前后端协同集成（推荐）
   - 后端：Spring Boot + uap-starter 接管认证
   - 前端：Vue3 处理跳转和用户状态
   - 适合：标准前后端分离项目（最常见场景）

C. 纯后端集成
   - 后端处理全部认证逻辑
   - 适合：传统 MPA 应用或无前端项目
```

使用 AskUserQuestion 工具，选项为：
- "模式 A：纯前端集成"
- "模式 B：前后端协同集成（推荐）"
- "模式 C：纯后端集成"

记录用户选择，进入第四阶段。

---

## 第四阶段：选择集成模块

根据所选模式，使用 AskUserQuestion（multiSelect: true）展示模块清单，让用户勾选需要生成的模块。

### 模式 B 模块清单（前后端协同）

**后端模块：**
- Maven 依赖（uap-starter + 三个 exclusion）
- application.yml 配置（uap.* 配置项）
- CommonController（getUserInfo + logout 接口）

**前端模块：**
- UapUser TypeScript 类型定义
- axios 响应拦截器（处理 ret=302 跳转）
- commonApi（getUserInfo + logout）
- Pinia user store
- 路由守卫（beforeEach 自动获取用户信息）
- Header 组件（用户名展示 + 退出按钮）
- public/config.js（后端地址注入）

默认全选，用户可取消不需要的模块。

### 模式 A 模块清单（纯前端）

- UapUser TypeScript 类型定义
- axios 响应拦截器（处理 ret=302 跳转）
- commonApi（getUserInfo + logout）
- Pinia user store
- 路由守卫（beforeEach 自动获取用户信息）
- Header 组件（用户名展示 + 退出按钮）
- public/config.js（后端地址注入）

### 模式 C 模块清单（纯后端）

- Maven 依赖（uap-starter + 三个 exclusion）
- application.yml 配置（uap.* 配置项）
- CommonController（getUserInfo + logout 接口）

---

## 第五阶段：逐模块生成

对每个用户选中的模块，按以下步骤执行：

### 5.1 说明阶段

向用户说明：
- 将要生成的文件路径（如 `src/main/java/com/example/controller/CommonController.java`）
- 文件的作用
- 若文件已存在，说明将要修改的内容

### 5.2 确认阶段

使用 AskUserQuestion 询问：
- "生成" → 继续
- "跳过此模块" → 跳过，处理下一个模块
- "修改写入路径" → 询问用户输入目标路径后继续

### 5.3 生成阶段

**内置模板模式：**

读取 `spring-boot-vue3-templates.md` 中对应的模板（使用 Read 工具），替换以下占位符后写入目标文件：

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{UAP_HOST}` | UAP 服务器地址 | `192.168.1.100` |
| `{UAP_PORT}` | UAP 服务器端口 | `8080` |
| `{BACKEND_HOST}` | 本应用后端地址 | `localhost` |
| `{BACKEND_PORT}` | 本应用后端端口 | `8081` |
| `{context-path}` | 后端 context-path | `api` |
| `{FRONTEND_HOST}` | 前端地址 | `localhost` |
| `{FRONTEND_PORT}` | 前端端口 | `3000` |
| `{your-app-code}` | 应用编码 | 从 UAP Manager 获取 |
| `{your-app-auth-code}` | 应用授权码 | 从 UAP Manager 获取 |

若用户尚未提供这些值，在生成前询问用户，或保留占位符并在文件中添加注释说明需要替换。

**文档驱动模式：**

根据第一阶段读取的 UAP 文档，提取对应接口信息，生成适配当前技术栈的代码。

### 5.4 完成阶段

所有模块生成完毕后：

1. 展示集成 Checklist（读取 `spring-boot-vue3-templates.md` 中的 Checklist 部分）
2. 展示常见问题（读取 `spring-boot-vue3-templates.md` 中的常见问题部分）
3. 提示用户：
   - 在 UAP Manager 中注册应用，获取 `app-code` 和 `app-auth-code`
   - 确认 `uap.cas-client-context` 与实际后端地址完全一致
   - 前端 axios 需设置 `withCredentials: true`

---

## 参考资源

### spring-boot-vue3-templates.md
内置 Spring Boot + Vue3 代码模板，包含 13 个模块的完整代码。在第五阶段生成代码时使用 Read 工具读取此文件。

### docs/
用户提供的 UAP 文档目录，详见 `docs/README.md` 中的配置说明。文档驱动模式下使用。
