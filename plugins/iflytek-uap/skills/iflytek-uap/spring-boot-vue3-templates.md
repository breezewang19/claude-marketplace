# Spring Boot + Vue3 内置模板

> 提炼自已验证项目（lw-aqsj、lw-tysjgl），适用于 Spring Boot + Vue3 前后端分离项目。

---

## 后端模板

### 模板 B1：Maven 依赖

```xml
<properties>
    <uap.version>V3.3.1</uap.version>
</properties>

<dependency>
    <groupId>com.iflytek.sec</groupId>
    <artifactId>uap-starter</artifactId>
    <version>${uap.version}</version>
    <exclusions>
        <!-- 必须排除，否则与项目依赖冲突 -->
        <exclusion>
            <groupId>com.iflytek.tuling</groupId>
            <artifactId>tuling-isvp-sdk</artifactId>
        </exclusion>
        <exclusion>
            <artifactId>fastjson</artifactId>
            <groupId>com.alibaba</groupId>
        </exclusion>
        <exclusion>
            <artifactId>swagger-annotations</artifactId>
            <groupId>io.swagger</groupId>
        </exclusion>
    </exclusions>
</dependency>
```

### 模板 B2：application.yml 配置

```yaml
spring:
  session:
    store-type: none  # 不使用Redis时设为none，生产环境建议改为redis

uap:
  # UAP Server 地址（找运维确认）
  cas-server-context: http://{UAP_HOST}:{UAP_PORT}/uap-server/
  # UAP REST API 地址
  rest-server-url: http://{UAP_HOST}:{UAP_PORT}/uap-server/rest/
  # 本应用后端地址（含context-path）
  cas-client-context: http://{BACKEND_HOST}:{BACKEND_PORT}/{context-path}
  # 登录成功后跳转的前端地址（前后端分离时必配）
  client-redirect-url: http://{FRONTEND_HOST}:{FRONTEND_PORT}/{frontend-path}
  # 应用编码（在 uap-manager 应用管理中查看）
  app-code: {your-app-code}
  # 应用授权码（在 uap-manager 应用管理中查看）
  app-auth-code: {your-app-auth-code}
  # 跨域白名单（前后端分离时，填前端地址）
  allowed-origins: http://{FRONTEND_HOST}:{FRONTEND_PORT}
  # 拦截白名单（不需要登录的路径，逗号分隔）
  # session-filter-exclude: /swagger-ui,/v3,/api/health
```

### 模板 B3：CommonController

```java
package com.iflytek.{module}.controller;

import com.iflytek.sec.uap.client.api.UapUserInfoAPI;
import com.iflytek.sec.uap.client.core.dto.user.UapUser;
import com.iflytek.sec.uap.client.util.LoginCommonUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

@Slf4j
@RestController
@RequestMapping("/common")
@RequiredArgsConstructor
public class CommonController {

    @GetMapping(value = "/getUserInfo")
    public YourResult<UapUser> getUserInfo(HttpServletRequest request) {
        return YourResult.success(UapUserInfoAPI.getLoginUser(request));
    }

    @GetMapping(value = "/logout")
    public void logout(HttpServletRequest request, HttpServletResponse response) throws IOException {
        UapUserInfoAPI.logout(request, response);
        LoginCommonUtil.redirectLogoutUrl(request, response);
    }
}
```

> `YourResult<T>` 替换为项目自己的统一响应类（如 `Result<T>`、`ApiResponse<T>`）。

### 模板 B4：UAP SDK API 速查

| 方法 | 说明 |
|------|------|
| `UapUserInfoAPI.getLoginUser(request)` | 从 session 获取当前登录用户（返回 `UapUser`） |
| `UapUserInfoAPI.logout(request, response)` | 清除本地 session |
| `LoginCommonUtil.redirectLogoutUrl(request, response)` | 重定向到 UAP 统一登出页 |

`UapUser` 常用字段：`loginName`, `name`, `phone`, `email`, `orgId`, `orgName`, `userId`

---

## 前端模板

### 模板 F1：UapUser TypeScript 类型

```typescript
// types.ts
export interface UapUser {
  id: string
  name: string
  loginName: string
  userType: number
  userTypeText?: string
  userSource?: number
  phone?: string
  address?: string
  email?: string
  status?: number
  orgId?: string
  orgCode?: string
  orgName?: string
  remark?: string
  birthday?: string
  createTime?: string
  updateTime?: string
  idNumber?: string
  extInfo?: string
  thirdExtInfo?: string
  profile?: string
}
```

### 模板 F2：axios 响应拦截器

```typescript
// 响应类型需包含 ret 和 redirectUrl
interface ApiResponse<T = any> {
  code: number
  data: T
  message: string
  ret?: number          // UAP 返回 302 表示未登录
  redirectUrl?: string  // UAP 登录页完整地址
}

// 响应拦截器
instance.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const { code, data, message, redirectUrl, ret } = response.data
    // ★ UAP 未登录拦截：ret=302 时跳转到 UAP 登录页
    if (ret === 302 && redirectUrl) {
      window.location.href = redirectUrl
      return new Promise(() => {}) // 阻断后续逻辑
    }
    // 正常业务处理...
    if (code === 200 || code === 0) {
      return data
    }
    return Promise.reject(new Error(message || '请求失败'))
  },
  (error) => {
    // 也要处理 HTTP 302（某些情况下 UAP 直接返回 HTTP 302）
    if (error.response?.status === 302) {
      const redirectUrl = error.response.headers['location']
      if (redirectUrl) {
        window.location.href = redirectUrl
      }
      return Promise.reject(new Error('需要重新登录'))
    }
    // 其他错误处理...
    return Promise.reject(error)
  },
)
```

### 模板 F3：API 接口定义

```typescript
// urls.ts
export const COMMON_URLS = {
  userInfo: '/common/getUserInfo',
  logout: '/common/logout',
}

// services.ts
export const commonApi = {
  getUserInfo: () => get<UapUser>(COMMON_URLS.userInfo),
  logout: () => get<void>(COMMON_URLS.logout),
}
```

### 模板 F4：Pinia user store

```typescript
// stores/user.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UapUser } from '@/api/types'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref<UapUser | null>(null)
  const userName = computed(() => userInfo.value?.name ?? '')

  function setUserInfo(user: UapUser | null) {
    userInfo.value = user
  }

  function clearUserInfo() {
    userInfo.value = null
    localStorage.clear()
    sessionStorage.clear()
  }

  return { userInfo, userName, setUserInfo, clearUserInfo }
})
```

### 模板 F5：路由守卫

```typescript
// router/index.ts
router.beforeEach(async (to, _from, next) => {
  if (to.meta.requiresAuth) {
    const userStore = useUserStore()
    if (!userStore.userInfo) {
      // 调用 getUserInfo，如果未登录会被 axios 拦截器自动跳转 UAP
      const user = await commonApi.getUserInfo()
      userStore.setUserInfo(user)
    }
  }
  next()
})
```

### 模板 F6：Header 组件

```vue
<template>
  <header class="app-header">
    <span class="username">{{ username }}</span>
    <button class="logout-btn" @click="handleLogout">退出登录</button>
  </header>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { commonApi } from '@/api/services'

const username = ref('')

onMounted(async () => {
  const user = await commonApi.getUserInfo()
  username.value = user?.name || user?.loginName || '未知用户'
})

const handleLogout = async () => {
  await commonApi.logout()
  localStorage.clear()
  sessionStorage.clear()
}
</script>
```

### 模板 F7：前端环境配置

```javascript
// public/config.js — 通过 window 全局变量注入，方便部署时修改
window.APP_CONFIG = {
  apiBaseUrl: 'http://{BACKEND_HOST}:{BACKEND_PORT}/{context-path}'
}
// 或按环境区分：
// development: '/api/{context-path}'  (配合 vite proxy)
// production:  'http://172.31.x.x:8080/{context-path}'
```

---

## 集成 Checklist

### 后端
- [ ] 添加 `uap-starter` Maven 依赖（含三个 exclusion）
- [ ] 配置 `application.yml` 中 `uap.*` 和 `spring.session.store-type`
- [ ] 创建 `CommonController`（getUserInfo + logout）
- [ ] 确认 `server.servlet.context-path` 与 `uap.cas-client-context` 一致
- [ ] 在 UAP Manager 中注册应用，获取 `app-code` 和 `app-auth-code`

### 前端
- [ ] 定义 `UapUser` TypeScript 类型
- [ ] axios 响应拦截器处理 `ret === 302 && redirectUrl` 跳转
- [ ] 创建 `commonApi`（getUserInfo + logout）
- [ ] 创建 Pinia user store
- [ ] 路由守卫中调用 getUserInfo（未登录会自动跳 UAP）
- [ ] Header 组件展示用户名和退出按钮
- [ ] `public/config.js` 配置后端 API 地址

---

## 常见问题

### Q1: 前后端跨域问题
配置 `uap.allowed-origins` 为前端地址。后端也可额外加 CorsConfig，但 uap-starter 自带跨域支持。

### Q2: 登录后页面空白/循环跳转
检查 `uap.cas-client-context` 是否与实际后端地址完全一致（含 context-path）。
检查 `uap.client-redirect-url` 是否为前端可访问的地址。

### Q3: getUserInfo 返回 null
确认请求携带了 cookie（axios 需设置 `withCredentials: true`，或前后端同域）。

### Q4: swagger-ui 被 UAP 拦截
在 `uap.session-filter-exclude` 中添加 `/swagger-ui,/v3,/webjars`。

### Q5: Spring Boot 版本兼容
已验证兼容：Spring Boot 2.6.6 和 2.7.15。JDK 1.8。
