# BaseResponse 响应基础类使用指南

> **迁移说明（2026-02）：** 本项目已迁移到 `yweb.response.Resp` 统一响应工具，不再使用 `app.api.base_response`。
> 本文中的响应格式和概念仍然适用，但 **导入路径和函数调用方式** 需替换为以下写法：
>
> ```python
> # ❌ 旧写法（已废弃）
> from app.api.base_response import OK, BadRequest, NotFound
>
> # ✅ 新写法
> from yweb.response import Resp
>
> return Resp.OK(data=user, message="查询成功")
> return Resp.BadRequest(message="参数错误")
> return Resp.NotFound(message="用户不存在")
> ```
>
> **新旧对应关系速查：**
>
> | 旧写法 | 新写法 |
> |--------|--------|
> | `OK(data, message)` | `Resp.OK(data, message)` |
> | `BadRequest(message, details)` | `Resp.BadRequest(message=msg)` |
> | `NotFound(message)` | `Resp.NotFound(message=msg)` |
> | `Unauthorized(message)` | `Resp.Unauthorized(message=msg)` |
> | `Forbidden(message)` | `Resp.Forbidden(message=msg)` |
> | `InternalServerError(message)` | `Resp.InternalServerError(message=msg)` |
>
> 分页响应使用 `PageResponse` 配合 DTO：
> ```python
> from yweb.response import Resp, PageResponse
> from yweb import DTO
>
> return Resp.OK(UserResponse.from_page(page_result))
> ```
>
> 详细规范请参考 `yweb-core/docs/webapi项目开发规范/dto_response_guide.md`。

---

## 概述

BaseResponse 是一个标准化的 API 响应工具类，提供了一致、规范的响应格式，支持成功响应、错误响应、分页响应等多种场景。

## 文件结构

- ~~`base_response.py`~~ — 已迁移到 `yweb.response.Resp`
- `BaseResponse_Usage_Guide.md` - 本使用指南（以下内容为通用响应规范参考）

## 响应格式标准

所有响应都遵循统一的 JSON 格式：

```json
{
    "status": "success",           // 响应状态，自动生成
    "message": "响应消息",          // 响应消息标题
    "msg_details": ["响应消息详情"], // 响应消息详情，可以为空
    "data": {}                     // 响应数据
}
```

### 字段说明

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `status` | string | ✅ | 响应状态，自动根据函数生成：`OK()`→"success"，`BadRequest()`→"error"，`Warning()`→"warning"，`Info()`→"info" |
| `message` | string | ✅ | 响应消息标题 |
| `msg_details` | array | ❌ | 响应消息详情，可以为空，主要放置详细的错误信息或警告 |
| `data` | object/array | ❌ | 响应数据，分页数据也统一放在这个字段中 |

> **提示：** 响应数据 `status` 用于前端弹窗，区分弹窗的类型。

## 快速开始

### 1. 导入响应函数

```python
# 最常用的简化别名
from app.api.base_response import OK, BadRequest, NotFound, Unauthorized, Forbidden, InternalServerError

# 扩展状态响应
from app.api.base_response import Warning, Info
```

### 2. 基本使用示例

```python
from fastapi import FastAPI
from app.api.base_response import OK, BadRequest, NotFound

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    """获取用户信息"""
    if user_id == 1:
        return OK({"id": 1, "name": "Tom"}, "用户获取成功")
    else:
        return NotFound(f"用户ID {user_id} 不存在")

@app.post("/users")
def create_user(user_data: dict):
    """创建用户"""
    try:
        # 模拟创建逻辑
        new_user = {"id": 3, "name": user_data.get("name")}
        return OK(new_user, "用户创建成功")
    except Exception as e:
        return BadRequest("创建用户失败", [str(e)])
```

### 3. OK() 函数参数说明

`OK()` 函数的参数顺序为 `OK(data, message)`，支持以下调用方式：

```python
# 只传 data（使用默认 message "请求成功"）
return OK(user_data)

# 传 data 和自定义 message
return OK(user_data, "查询成功")

# 使用命名参数
return OK(data=user_data, message="查询成功")
```

### ⚠️ 重要：参数顺序差异

**`OK()` 与其他响应函数的参数顺序不同**，请注意区分：

| 函数类型 | 参数顺序 | 设计理由 |
|----------|----------|----------|
| `OK()` | `data, message` | 核心目的是**返回数据**，data 最常用 |
| 其他函数 | `message, ...` | 核心目的是**传递消息**，message 最重要 |

```python
# ✅ OK - data 在前（返回数据为主）
return OK(user)                              # data 在前，message 用默认值
return OK(page_result, "查询成功")

# ✅ 错误响应 - message 在前（传递错误信息为主）
return BadRequest("参数错误")
return BadRequest("验证失败", ["用户名不能为空", "密码太短"])
return NotFound("用户不存在")

# ✅ 扩展响应 - message 在前
return Warning("导入有警告", data=result, msg_details=["第3行格式错误"])
return Info("系统将于今晚维护")
```

## 响应类型详解

### 成功响应 (2xx)

统一使用 `OK()` 方法处理所有成功响应，HTTP状态码统一使用200。

| 函数        | HTTP状态码 | 用途                       | 示例                                                                 |
| ----------- | ---------- | -------------------------- | -------------------------------------------------------------------- |
| `OK()`      | 200        | 通用成功响应               | `OK({"user": user_data}, "登录成功")`                                |
| `Warning()` | 200        | 警告响应（操作成功但有警告） | `Warning("导入完成，部分数据格式异常", msg_details=["第3行邮箱格式不正确"])` |
| `Info()`    | 200        | 信息响应（纯信息性消息）     | `Info("系统将于今晚12点进行维护")`                                    |


### 客户端错误响应 (4xx)

| 函数               | HTTP状态码 | 用途       | 示例                                               |
| ------------------ | ---------- | ---------- | -------------------------------------------------- |
| `BadRequest()`     | 400        | 客户端错误 | `BadRequest("参数错误", ["用户名不能为空"])`       |
| `Unauthorized()`   | 401        | 未认证     | `Unauthorized("请先登录")`                         |
| `Forbidden()`      | 403        | 无权限     | `Forbidden("无权限访问该资源")`                    |
| `NotFound()`       | 404        | 资源不存在 | `NotFound("用户不存在")`                           |
| `Conflict()`       | 409        | 资源冲突   | `Conflict("用户名已存在")`                         |
| `TooManyRequests()`| 429        | 限流       | `TooManyRequests("操作过于频繁，请稍后再试")`      |

### 服务端错误响应 (5xx)

| 函数                    | HTTP状态码 | 用途       | 示例                                                           |
| ----------------------- | ---------- | ---------- | -------------------------------------------------------------- |
| `InternalServerError()` | 500        | 服务器错误 | `InternalServerError("数据库连接失败", ["数据库连接超时"])`    |

### 扩展状态使用示例

```python
from app.api.base_response import OK, Warning, Info, BadRequest

# 批量导入 - 有警告的成功
@app.post("/users/batch-import")
def batch_import_users(file: UploadFile):
    result = process_batch_import(file)
    if result["has_warnings"]:
        return Warning(
            "批量导入完成，但有警告信息",
            data={"imported_count": result["success"]},
            msg_details=["第3行邮箱格式不规范，已自动修正", "第7行手机号格式异常"]
        )
    return OK({"imported_count": result["success"]}, "批量导入成功")

# 系统公告
@app.get("/system/notice")
def get_system_notice():
    notice = get_current_notice()
    if notice:
        return Info("系统公告", data=notice)
    return Info("暂无系统公告")
```

## 分页响应

### 使用 OK() 返回分页数据

分页查询直接使用 `OK()` 配合 `Page` 对象返回，系统会自动序列化：

```python
from app.api.base_response import OK

@app.get("/users")
def get_users(page: int = 1, page_size: int = 10):
    """获取用户列表（分页）"""
    # 使用 Model.query.paginate() 返回 Page 对象
    page_result = User.query.paginate(page=page, page_size=page_size)
    
    # 直接返回 Page 对象，会自动序列化
    return OK(page_result, "用户列表获取成功")
```

### 分页响应格式

```json
{
    "status": "success",
    "message": "用户列表获取成功",
    "msg_details": [],
    "data": {
        "rows": [
            {"id": 1, "name": "Tom"},
            {"id": 2, "name": "Jerry"}
        ],
        "total_records": 100,
        "page": 1,
        "page_size": 10,
        "total_pages": 10,
        "has_prev": false,
        "has_next": true
    }
}
```

### 自动序列化特性

`OK()` 函数支持自动序列化以下类型：
- **DTO 对象**：自动调用 `to_dict()` 方法
- **SQLAlchemy 模型**：自动提取所有列属性
- **Page 分页对象**：自动序列化分页信息和 rows 中的每个对象
- **datetime 对象**：自动格式化为 `YYYY-MM-DD HH:MM:SS` 字符串
- **列表/字典**：递归处理每个元素

## 高级用法

### 自定义错误信息

```python
# 单个错误
return BadRequest("邮箱格式不正确")

# 多个错误详情
errors = [
    "用户名长度不能少于3个字符",
    "密码必须包含数字和字母",
    "邮箱格式不正确"
]
return BadRequest("注册信息验证失败", errors)
```

### 完整类导入（不建议使用此方法）

```python
# 导入完整的响应类
from app.api.base_response import (
    SuccessResponse,      # 成功响应类
    ClientErrorResponse,  # 客户端错误类
    ServerErrorResponse,  # 服务端错误类
    ExtendedResponse      # 扩展响应类
)

# 使用类方法
return SuccessResponse.OK(data, "操作成功")
return ClientErrorResponse.NotFound("资源不存在")
return ServerErrorResponse.InternalServerError("服务器错误")

## HTTP状态码与业务状态码的关系

### 两者的区别与联系

**HTTP状态码**（如200, 400, 500）表示**HTTP协议层面**的响应状态，告诉客户端请求是否被成功接收、理解和处理。

**业务状态码**（如success, error, partial_success）表示**业务逻辑层面**的处理结果，描述具体的业务操作是否成功以及成功/失败的具体类型。

### 使用原则

#### 1. HTTP状态码优先
- **2xx**：请求被成功接收和处理
- **4xx**：客户端请求有问题
- **5xx**：服务端处理出错

#### 2. 业务状态表示例
业务状态现在通过 `message` 和 `data` 字段来表达，不再使用单独的 `status` 字段：

```python
# ✅ 正确：HTTP 200表示请求成功，通过message和data表达业务状态
HTTP 200 + message: "批量导入完成，成功8条，失败2条"  # 批量导入部分成功

# ✅ 正确：HTTP 200表示请求成功，通过message和data表达警告信息  
HTTP 200 + message: "数据导入成功，但部分数据格式已修正"  # 数据导入成功但有格式警告

# ✅ 正确：HTTP 500表示服务不可用，通过message表达重试建议
HTTP 500 + message: "服务暂时不可用，请稍后重试"      # 服务暂时不可用，建议重试

# ❌ 错误：HTTP 400表示请求错误，但message表明成功
HTTP 400 + message: "操作成功"                       # ❌ 矛盾的组合
```

### 常见组合模式

| 场景         | HTTP状态码 | 使用函数 | 参数顺序 | 示例                     |
| ------------ | ---------- | -------- | -------- | ------------------------ |
| 完全成功     | 200        | `OK()` | data, message | 用户登录成功             |
| 有警告的成功 | 200        | `Warning()` | message, data, msg_details | 数据导入成功但有格式警告 |
| 信息提示     | 200        | `Info()` | message, data | 系统维护通知             |
| 业务验证失败 | 400        | `BadRequest()` | message, msg_details | 用户名已存在     |
| 系统错误     | 500        | `InternalServerError()` | message, msg_details | 数据库连接失败   |

### 前端处理建议

```javascript
// 前端应该优先检查HTTP状态码
if (response.status === 200) {
    // 再检查业务状态码
    if (response.data.status === "partial_success") {
        // 处理部分成功的情况
        showWarning(`成功${response.data.data.success_count}条，失败${response.data.data.fail_count}条`);
    } else if (response.data.status === "warning") {
        // 处理警告情况
        showWarning(response.data.message);
    } else {
        // 完全成功
        showSuccess(response.data.message);
    }
} else if (response.status >= 400) {
    // HTTP错误，显示错误信息
    showError(response.data.message);
}
```

#### 状态码选择决策树

```
请求是否成功到达服务器？
├── 否 → 使用HTTP错误码（4xx/5xx）
└── 是 → 业务处理结果如何？
    ├── 完全成功 → message + data
    ├── 部分成功 → message + data
    ├── 有警告 → message + data
    ├── 纯信息 → message + data
    ├── 业务验证失败 → message + msg_details
    ├── 系统错误 → message + msg_details
    ├── 异步处理中 → message + data
    ├── 需要重试 → message + data
    ├── 已取消 → message + data
    ├── 超时 → message + data
    └── 已弃用 → message + data
```

## 最佳实践

### 1. 统一响应格式

所有API接口都应该使用BaseResponse提供的响应格式，确保一致性。

### 2. 有意义的错误消息

提供清晰、具体的错误信息，帮助前端开发者理解问题。

```python
# ❌ 不推荐的通用错误
return BadRequest("参数错误")

# ✅ 推荐的具体错误
return BadRequest("手机号格式不正确，请输入11位手机号码")
```

### 3. 错误详情数组

对于表单验证等场景，使用errors数组返回多个错误详情。

```python
errors = []
if not username:
    errors.append("用户名不能为空")
if len(password) < 6:
    errors.append("密码长度不能少于6位")
if not email.contains("@"):
    errors.append("邮箱格式不正确")

if errors:
    return BadRequest("注册信息验证失败", errors)
```

### 4. 分页标准化

所有列表接口都应该使用分页响应，保持一致的分页格式。

```python
@app.get("/items")
def get_items(page: int = 1, page_size: int = 20):
    items, total = query_items(page, page_size)
    return PaginatedResponse(items, total, page, page_size)
```

### 5. 状态码选择

选择合适的HTTP状态码，遵循RESTful设计原则。

- 2xx - 成功：操作成功完成
- 4xx - 客户端错误：请求有问题
- 5xx - 服务端错误：服务器处理失败

## 完整示例

```python
from fastapi import FastAPI
from typing import Optional
from app.api.base_response import (
    OK, BadRequest, NotFound, Unauthorized, Forbidden,
    Warning, Info, InternalServerError
)

app = FastAPI()

# 用户管理示例
@app.post("/auth/login")
def login(username: str, password: str):
    """用户登录"""
    if not username or not password:
        return BadRequest("用户名和密码不能为空")
  
    # 验证用户
    user = authenticate_user(username, password)
    if not user:
        return Unauthorized("用户名或密码错误")
  
    # 生成token
    token = generate_token(user)
    return OK({"token": token, "user": user}, "登录成功")

@app.get("/users")
def list_users(
    page: int = 1, 
    page_size: int = 10,
    search: Optional[str] = None
):
    """用户列表"""
    # 使用分页查询
    page_result = User.query.paginate(page=page, page_size=page_size)
    return OK(page_result, "用户列表获取成功")

@app.get("/users/{user_id}")
def get_user_detail(user_id: int):
    """用户详情"""
    user = get_user_by_id(user_id)
    if not user:
        return NotFound(f"用户ID {user_id} 不存在")
  
    return OK(user, "用户详情获取成功")

@app.post("/users")
def create_user(user_data: dict):
    """创建用户"""
    # 参数验证
    errors = validate_user_data(user_data)
    if errors:
        return BadRequest("用户数据验证失败", errors)
  
    # 检查用户名是否存在
    if user_exists(user_data["username"]):
        return BadRequest("用户名已存在")
  
    # 创建用户
    try:
        new_user = create_user_in_db(user_data)
        return OK(new_user, "用户创建成功")
    except Exception as e:
        return BadRequest("创建用户失败", [str(e)])

@app.put("/users/{user_id}")
def update_user(user_id: int, user_data: dict):
    """更新用户"""
    # 检查用户是否存在
    if not user_exists_by_id(user_id):
        return NotFound(f"用户ID {user_id} 不存在")
  
    # 验证数据
    errors = validate_user_data(user_data, update=True)
    if errors:
        return BadRequest("用户数据验证失败", errors)
  
    # 更新用户
    try:
        updated_user = update_user_in_db(user_id, user_data)
        return OK(updated_user, "用户更新成功")
    except Exception as e:
        return BadRequest("更新用户失败", [str(e)])

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """删除用户"""
    if not user_exists_by_id(user_id):
        return NotFound(f"用户ID {user_id} 不存在")
  
    try:
        delete_user_from_db(user_id)
        return OK({"id": user_id}, "用户删除成功")
    except Exception as e:
        return BadRequest("删除用户失败", [str(e)])

# 权限控制示例
@app.get("/admin/users")
def admin_list_users():
    """管理员用户列表"""
    if not current_user.is_admin:
        return Forbidden("需要管理员权限")
  
    users = get_all_users()
    return OK(users, "管理员用户列表")

# 批量导入示例
@app.post("/users/batch-import")
def batch_import_users(file: UploadFile):
    """批量导入用户"""
    if not file.filename.endswith('.xlsx'):
        return BadRequest("仅支持Excel文件格式")
  
    result = process_batch_import(file)
  
    if result.get("has_warnings"):
        return Warning(
            f"批量导入完成，成功{result['success']}条",
            data={"success_count": result["success"]},
            msg_details=result.get("warnings", [])
        )
    elif result["status"] == "failed":
        return BadRequest("批量导入失败", [result["error"]])
  
    return OK({"imported_count": result["success"]}, "批量导入成功")

@app.get("/system/notice")
def get_system_notice():
    """获取系统公告"""
    notice = get_current_notice()
    if notice:
        return Info("系统公告", data=notice)
    return Info("暂无系统公告")
```

## 13. 前后端接口交互规范

### 13.1 请求规范

#### URL格式

```javascript
// 基础请求URL
const url = '/api/v1/users'

// GET请求参数示例
url = '/api/v1/users?page_index=1&page_size=10'
url = '/api/v1/users/1'  // 请求单个用户信息
```

#### 请求头参数

```javascript
const header = {
  'authorization': 'Bearer ' + token,  // 认证token
  'Content-Type': 'application/json'     // 默认内容类型
}
```

#### 请求体参数结构

```javascript
const reqparams = {
  "action": "create|update|delete|search|upload|download",  // 操作类型
  "data": {},      // 普通请求数据
  "file": file,    // 上传文件时的二进制数据
  "page_index": 1, // 可选，分页参数
  "page_size": 10  // 可选，分页参数
}
```

### 13.2 文件操作

#### 文件上传

```javascript
const url = '/api/upload?uid=123'
const formData = new FormData()
formData.append('file', file)  // file为文件对象

// 发送请求
fetch(url, {
  method: 'POST',
  body: formData,
  headers: {
    'authorization': 'Bearer ' + token
  }
})
```

#### 文件下载

```javascript
const url = '/api/download'

// 下载文件接口请求头参数示例：
const req = {
  file: file  // 文件对象
}

// 下载请求
fetch(url, {
  method: 'GET',
  headers: {
    'authorization': 'Bearer ' + token
  }
})
.then(response => response.blob())
.then(blob => {
  // 处理下载的文件
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'filename.ext'
  a.click()
})
```

### 13.3 WebSocket连接

```javascript
// WebSocket连接示例
let SOCKET_URL = "ws://192.168.50.131/ws/1/workflow"

const ws = new WebSocket(SOCKET_URL)

// 连接成功
ws.onopen = function(event) {
  console.log("连接成功")
  // 发送消息
  ws.send(JSON.stringify({
    action: 'create',
    data: { name: "张三", age: 20 }
  }))
}

// 接收消息
ws.onmessage = function(event) {
  const data = JSON.parse(event.data)
  console.log('收到消息：', data)
}

// 错误处理
ws.onerror = function(event) {
  console.error('WebSocket 错误:', event)
}

// 连接关闭
ws.onclose = function(event) {
  console.log('关闭连接：', event)
}

```

### 13.4 响应规范

#### 响应头参数

```javascript
const responsheader = {
  "x-new-token": "new_token",  // 新token，存在则替换旧的token
  "Content-Type": "application/json"
}
```

#### 响应体参数结构

```javascript
const responseparams = {
  "status": "success",                                     // 响应状态，自动生成
  "message": "响应消息",                                    // 状态描述
  "msg_details": [],                                       // 响应消息详情
  "data": {}                                               // 普通返回数据，分页数据也统一放在这里
}
```

### 13.5 HTTP状态码使用规范

| HTTP状态码 | 含义说明       |
| ---------- | -------------- |
| 200        | 请求成功（包括创建、更新、删除等操作） |
| 400        | 客户端错误     |
| 401        | 未认证         |
| 403        | 无权限         |
| 404        | 资源不存在     |
| 409        | 资源冲突       |
| 429        | 限流           |
| 500        | 服务器错误     |

### 13.6 业务状态表示例

业务状态信息通过 `message` 和 `data` 字段来表达

| 业务状态 | 实现方式 | 使用场景 | 示例 |
| -------- | -------- | -------- | ---- |
| 成功 | data + message | 所有操作成功完成 | 用户登录成功、数据查询成功 |
| 失败 | message + msg_details | 操作失败 | 参数验证失败、业务规则不满足 |
| 警告 | message + data + msg_details | 操作成功但有警告信息 | 数据导入成功但有格式警告 |
| 信息 | message + data | 纯信息性消息 | 系统公告、维护通知 |

#### 业务状态示例

```python
# 部分成功 - 批量操作
return BaseResponse._create_response(
    message="批量导入完成，成功8条，失败2条",
    data={
        "success_count": 8,
        "fail_count": 2,
        "fail_items": [
            {"row": 3, "reason": "邮箱格式错误"},
            {"row": 7, "reason": "手机号已存在"}
        ]
    }
)

# 处理中 - 异步任务
return BaseResponse._create_response(
    message="视频转码中，请稍候...",
    data={
        "task_id": "task_12345",
        "progress": 45,  # 进度百分比
        "estimated_time": 120  # 预计剩余时间（秒）
    }
)

# 需要重试 - 临时失败
return BaseResponse._create_response(
    message="服务暂时不可用，请稍后重试",
    data={
        "retry_after": 30,  # 建议重试间隔（秒）
        "retry_count": 3    # 建议重试次数
    }
)

# 已弃用 - API警告
return BaseResponse._create_response(
    message="此API版本已弃用，请升级到v2.0",
    data={
        "deprecated_version": "v1.0",
        "recommended_version": "v2.0",
        "deprecation_date": "2024-12-31"
    }
)
```

### 13.7 错误处理规范

#### 单错误响应

```json
{
  "status": "error",
  "message": "手机号格式不正确",
  "msg_details": [],
  "data": {}
}
```

#### 响应参数示例补充

```javascript
// 上传文件响应参数示例：
const response = {
  "status": "success",
  "message": "文件上传成功",
  "msg_details": [],
  "data": {
    "file_id": "12345",
    "file_url": "/files/12345.pdf",
    "file_size": 1024000
  }
}

// 下载文件响应参数示例：
const response = {
  "status": "success",
  "message": "文件下载成功",
  "msg_details": [],
  "data": {
    "file_name": "document.pdf",
    "download_url": "/download/12345"
  }
}
```

#### 多错误响应
```json
{
  "status": "error",
  "message": "注册信息验证失败",
  "msg_details": [
    "用户名长度不能少于3个字符",
    "密码必须包含数字和字母",
    "邮箱格式不正确"
  ],
  "data": {}
}
```

### 13.8 分页响应规范

#### 请求分页参数

```javascript
// URL参数方式
/api/v1/users?page_index=1&page_size=10

// 请求体方式
{
  "action": "search",
  "page_index": 1,
  "page_size": 10
}
```

#### 分页响应格式

```json
{
  "status": "success",
  "message": "数据获取成功",
  "msg_details": [],
  "data": {
    "rows": [
      {"id": 1, "name": "用户1"},
      {"id": 2, "name": "用户2"}
    ],
    "total_records": 100,
    "page": 1,
    "page_size": 10,
    "total_pages": 10,
    "has_prev": false,
    "has_next": true
  }
}
```

### 13.9 最佳实践

1. **统一使用BaseResponse**: 所有API响应都应该使用BaseResponse提供的标准化格式
2. **合理选择HTTP状态码**: 根据操作结果选择合适的状态码
3. **提供有意义的错误信息**: 错误信息应该具体、清晰，便于调试
4. **分页统一格式**: 所有列表接口都应该使用标准的分页格式
5. **token自动刷新**: 后端在响应头中返回新token时，前端应该自动更新
6. **WebSocket重连机制**: 实现断线重连逻辑，提高稳定性
7. **文件上传进度**: 大文件上传时应该显示上传进度
8. **错误统一处理**: 前端应该统一处理各类错误响应

### 13.10 简化别名使用示例

以下是所有简化别名的实际使用示例：

```python
from app.api.base_response import (
    # 成功响应
    OK,
    
    # 客户端错误响应
    BadRequest, Unauthorized, Forbidden, NotFound,
    
    # 服务端错误响应
    InternalServerError,
  
    # 扩展状态响应
    Warning, Info
)

# 成功响应示例（注意：data 在前，message 在后）
return OK(data)                              # 使用默认 message "请求成功"
return OK(data, "操作成功")                   # 自定义 message
return OK(new_user, "创建成功")
return OK(page_result, "查询成功")            # 分页数据

# 客户端错误响应示例
return BadRequest("参数错误", ["用户名不能为空", "密码太短"])
return Unauthorized("请先登录")
return Forbidden("无权限访问该资源")
return NotFound("用户不存在")

# 服务端错误响应示例
return InternalServerError("数据库连接失败", ["连接超时"])

# 扩展状态响应示例
return Warning("导入完成，部分数据格式异常", data=result, msg_details=["第3行邮箱格式已修正"])
return Info("系统将于今晚12点进行维护", data={"maintenance_time": "2024-01-01 00:00:00"})
```

## 总结

BaseResponse 提供了：

1. **统一的响应格式** - 所有API响应保持一致的结构 `{message, msg_details, data}`
2. **简洁的函数签名** - `OK(data, message)` data 在前，方便快速返回数据
3. **自动序列化** - 支持 DTO、SQLAlchemy 模型、Page 分页对象、datetime 的自动序列化
4. **丰富的响应类型** - 覆盖常见的 HTTP 状态码（200/400/401/403/404/409/429/500）
5. **详细的错误信息** - 通过 `msg_details` 支持多个错误详情返回
6. **完整的前后端交互规范** - 涵盖请求、响应、文件操作、WebSocket等场景

### 可用的响应函数

| 函数                  | HTTP状态码 | 参数                          |
| --------------------- | ---------- | ----------------------------- |
| `OK`                  | 200        | `(data, message)`             |
| `Warning`             | 200        | `(message, data, msg_details)`|
| `Info`                | 200        | `(message, data)`             |
| `BadRequest`          | 400        | `(message, msg_details)`      |
| `Unauthorized`        | 401        | `(message, msg_details)`      |
| `Forbidden`           | 403        | `(message, msg_details)`      |
| `NotFound`            | 404        | `(message, msg_details)`      |
| `Conflict`            | 409        | `(message, msg_details)`      |
| `TooManyRequests`     | 429        | `(message, msg_details)`      |
| `InternalServerError` | 500        | `(message, msg_details)`      |

使用 BaseResponse 和遵循这些交互规范可以让你的API响应更加规范、易维护，提升开发效率，确保前后端协作顺畅。
