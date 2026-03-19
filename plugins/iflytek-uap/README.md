# iflytek-uap

UAP 统一认证平台集成助手 - 引导式将 UAP 认证集成到项目中。

## 功能特性

- 支持两种代码生成方式：内置模板（Spring Boot + Vue3）和文档驱动（任意 UAP 版本）
- 自动检测项目技术栈（Spring Boot、Vue3/React/Angular、TypeScript）
- 三种集成模式：纯前端、前后端协同（推荐）、纯后端
- 逐模块生成，每步确认后再写入
- 内置集成 Checklist 和常见问题

## 使用方式

安装后，在 Claude Code 中输入 `/iflytek-uap` 即可启动。

## 文件结构

```
skills/iflytek-uap/
├── SKILL.md                          ← 主流程（5 个阶段）
├── spring-boot-vue3-templates.md     ← 内置代码模板（13 个模块）
└── docs/                             ← 放置 UAP 官方文档（用户自行添加）
    └── README.md                     ← 文档配置说明
```

## 内置模板模块

**后端（Spring Boot）：**
- Maven 依赖（uap-starter + exclusions）
- application.yml 配置
- CommonController（getUserInfo + logout）

**前端（Vue3 + TypeScript）：**
- UapUser 类型定义
- axios 响应拦截器（处理 ret=302 跳转）
- commonApi
- Pinia user store
- 路由守卫
- Header 组件
- public/config.js

## 文档驱动模式

如需使用文档驱动模式，将 UAP 官方文档放置到 `docs/` 目录：

| 文件 | 说明 |
|------|------|
| `uap-quick-reference.md` | 手动整理的关键信息（推荐） |
| `uap-integration-guide.pdf` | 官方集成指南 |
| `uap-api-reference.pdf` | 官方 API 参考文档 |

详见 `docs/README.md`。
