# UAP 文档目录

使用 `iflytek-uap` skill 前，请将 UAP 文档文件放置在此目录下。

## 所需文件

以下文件至少提供一个：

| 文件 | 说明 |
|------|------|
| `uap-quick-reference.md` | 手动整理的关键信息（推荐，读取最快） |
| `uap-integration-guide.pdf` | 官方集成指南 |
| `uap-api-reference.pdf` | 官方 API 参考文档 |

## 读取优先级

skill 按以下顺序读取文档：
1. `uap-quick-reference.md` — 存在时优先读取，效率最高
2. PDF 文件 — 使用 Read 工具解析（每次最多 20 页）

## 快速参考模板

如需自行创建 `uap-quick-reference.md`，可参考以下模板：

```markdown
# UAP 快速参考 vX.X

## 认证接口

### 登录（CAS）
- **接口：** POST /uap-server/api/v2/login
- **参数：** username、password（md5+rsa 加密）、orgId、service
- **返回：** `{ flag, code, message, data: { ticket } }`

### 验证 Ticket
- **接口：** GET /uap-server/api/v4/cas/validateTicket
- **查询参数：** ticket、service
- **返回：** `{ flag, code, message, data: { accessToken, refreshToken, expiresIn } }`

## Token 管理

### 验证 Token
- **接口：** GET /uap-server/api/v4/validateToken
- **请求头：** accessToken
- **返回：** `{ flag, code, message, data: { userInfo, tenantInfo } }`

### 刷新 Token
- **接口：** POST /uap-server/api/v4/refreshToken
- **请求体：** `{ refreshToken }`
- **返回：** `{ flag, code, message, data: { accessToken, expiresIn } }`

## 用户管理

### 获取用户信息
- **接口：** GET /uap-server/api/v4/getUserInfo
- **请求头：** accessToken

## 错误码
- 0：成功
- 401：未授权
- 1001：凭证无效
- 1002：账号已锁定
- 1003：Ticket 已过期
```

## 注意事项

- 此目录默认已加入 .gitignore，请勿提交公司内部文档
- UAP 版本更新时，只需替换此处的文档文件，skill 本身无需修改
