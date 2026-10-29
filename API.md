# 基于 AI 的个人健康饮食推荐系统接口文档

本文档基于 `backend/src/main/java/com/health/controller` 下实际控制器梳理，用于后端开发、前端联调、算法联调和接口自动化测试。

## 1. 基本信息

| 项目 | 说明 |
| --- | --- |
| 服务地址 | `http://127.0.0.1:8081` |
| Context Path | `/api` |
| 完整接口前缀 | `http://127.0.0.1:8081/api` |
| 数据格式 | `application/json;charset=UTF-8` |
| 认证方式 | JWT，请求头 `Authorization: Bearer <token>` |
| 时间格式 | `yyyy-MM-dd HH:mm:ss`，日期一般使用 `yyyy-MM-dd` |

## 2. 通用响应结构

成功和业务异常均返回统一 JSON 信封：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {}
}
```

部分健康分析接口除 `data` 外还会额外返回 `analysis`：

```json
{
  "code": 200,
  "message": "获取健康信息成功",
  "data": {},
  "analysis": {}
}
```

## 3. 通用状态码

| HTTP 状态码 | 业务 `code` | 含义 | 常见场景 |
| --- | --- | --- | --- |
| 200 | 200 | 成功 | 业务正常返回 |
| 400 | 400 | 请求参数或业务规则错误 | 登录失败、数据不存在、参数校验失败 |
| 401 | 401 | 未登录或 Token 过期 | 缺少 Token、Token 无效 |
| 403 | - | 权限不足 | 非管理员访问管理接口 |

## 4. 认证接口

### 4.1 注册

`POST /auth/register`

请求体：

```json
{
  "username": "test_user",
  "email": "test_user@example.com",
  "password": "123456",
  "phone": "13800138000"
}
```

成功响应：

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "token": "<jwt-token>",
    "userId": 1,
    "username": "test_user",
    "email": "test_user@example.com",
    "phone": "13800138000",
    "avatar": null,
    "role": "user"
  }
}
```

常见失败：

- `用户名已存在`
- `邮箱已被注册`
- `密码长度应在6-50之间`
- `邮箱格式不正确`

### 4.2 登录

`POST /auth/login`

请求体：

```json
{
  "email": "123456@qq.com",
  "password": "123456"
}
```

成功响应：

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "<jwt-token>",
    "userId": 2,
    "username": "张三",
    "email": "123456@qq.com",
    "role": "user"
  }
}
```

常见失败：

- `用户不存在`
- `密码错误`
- `账号已被禁用`

## 5. 用户接口

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| GET | `/user/profile` | 用户 | 获取当前用户资料 |
| PUT | `/user/profile` | 用户 | 更新用户名、手机号、头像 |
| GET | `/user/admin/list` | 管理员 | 获取用户列表 |
| PUT | `/user/admin/{userId}/status?status=0` | 管理员 | 启用/禁用用户 |
| GET | `/user/diet-preference` | 用户 | 获取饮食偏好 |
| PUT | `/user/diet-preference` | 用户 | 更新饮食偏好 |

### 5.1 获取个人资料

`GET /user/profile`

成功响应 `data`：

```json
{
  "userId": 2,
  "username": "张三",
  "email": "123456@qq.com",
  "phone": "19330406783",
  "avatar": null,
  "status": 1,
  "createTime": "2026-03-15 22:34:49",
  "updateTime": "2026-03-15 22:34:49",
  "role": "user"
}
```

## 6. 健康档案与饮食目标

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| POST | `/health/info` | 用户 | 新增或更新健康档案 |
| GET | `/health/info` | 用户 | 获取当前健康档案 |
| GET | `/health/history` | 用户 | 获取健康档案历史 |
| POST | `/health/goal` | 用户 | 新增或更新饮食目标 |
| GET | `/health/goal` | 用户 | 获取当前饮食目标 |

### 6.1 保存健康档案

`POST /health/info`

请求体：

```json
{
  "age": 24,
  "gender": "male",
  "height": 175.0,
  "weight": 68.0,
  "bmi": 22.2,
  "bmr": 1650.0,
  "bloodPressure": "120/80",
  "bloodSugar": 5.2,
  "activityLevel": "moderate",
  "exerciseDuration": 30,
  "exerciseType": "running",
  "chronicDiseases": ""
}
```

### 6.2 保存饮食目标

`POST /health/goal`

请求体：

```json
{
  "goalType": "maintain",
  "targetWeight": 68.0,
  "targetCalories": 2100.0,
  "proteinRatio": 0.20,
  "carbsRatio": 0.50,
  "fatRatio": 0.30,
  "proteinTarget": 105.0,
  "carbsTarget": 260.0,
  "fatTarget": 70.0,
  "waterTarget": 2000,
  "status": 1,
  "startDate": "2026-01-01",
  "endDate": "2026-12-31",
  "reminderEnabled": 1,
  "reminderTime": "08:00:00"
}
```

## 7. 饮食记录

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| POST | `/record/submit` | 用户 | 提交饮食记录 |
| GET | `/record/list` | 用户 | 分页获取饮食记录 |
| GET | `/record/detail/{recordId}` | 用户 | 获取饮食记录详情 |
| GET | `/record/analysis/trend` | 用户 | 获取摄入趋势分析 |
| DELETE | `/record/{recordId}` | 用户 | 删除饮食记录 |
| GET | `/record/suggestions` | 用户 | 获取饮食建议 |

### 7.1 提交饮食记录

`POST /record/submit`

请求体：

```json
{
  "date": "2026-09-08",
  "mealType": "breakfast",
  "notes": "早餐",
  "details": [
    {
      "foodName": "燕麦",
      "ingredientId": 1,
      "amount": 50,
      "unit": "g",
      "calories": 194,
      "protein": 6.6,
      "carbs": 33.5,
      "fat": 3.1
    }
  ]
}
```

### 7.2 记录列表

`GET /record/list?page=1&pageSize=10&startDate=2026-09-01&endDate=2026-09-08`

`data` 为饮食记录数组，每条记录包含：

- `id`、`userId`、`recordDate`、`mealType`
- `totalCalories`、`totalProtein`、`totalCarbs`、`totalFat`
- `details`：该餐次包含的食材明细

## 8. 食谱推荐

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| GET | `/recommend/recipes` | 用户 | 推荐早餐、午餐、晚餐食谱 |
| POST | `/recommend/ingredient/substitute` | 可选用户 | 获取食材替代建议 |
| POST | `/recommend/recipes/by-goal` | 用户 | 按目标推荐食谱 |
| GET | `/recommend/recipes/today` | 用户 | 获取今日推荐食谱 |

### 8.1 三餐推荐

`GET /recommend/recipes?breakfastCount=3&lunchCount=3&dinnerCount=3`

成功响应 `data`：

```json
{
  "breakfast": [],
  "lunch": [],
  "dinner": []
}
```

### 8.2 食材替代

`POST /recommend/ingredient/substitute`

请求体：

```json
{
  "ingredientName": "鸡胸肉",
  "prompt": "鸡胸肉可以用什么低脂食材替代"
}
```

## 9. 食谱管理

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| GET | `/recipe/list` | 无需认证 | 获取全部食谱 |
| GET | `/recipe/detail/{id}` | 无需认证 | 获取食谱详情 |
| GET | `/recipe/custom` | 用户 | 获取当前用户自定义食谱 |
| GET | `/recipe/search?keyword=鸡` | 无需认证 | 搜索食谱 |
| POST | `/recipe/save` | 用户 | 保存自定义食谱 |
| PUT | `/recipe/update` | 创建者或管理员 | 更新食谱 |
| DELETE | `/recipe/delete/{id}` | 创建者或管理员 | 删除食谱 |
| GET | `/recipe/nutrition/{id}` | 无需认证 | 获取食谱营养分析 |
| GET | `/recipe/recommend` | 无需认证 | 获取食谱推荐 |
| POST | `/recipe/collect/{recipeId}` | 用户 | 收藏食谱 |
| DELETE | `/recipe/collect/{recipeId}` | 用户 | 取消收藏 |
| GET | `/recipe/collect/status/{recipeId}` | 用户 | 查询收藏状态 |
| GET | `/recipe/collect/list` | 用户 | 获取收藏食谱 |

## 10. 食材管理

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| GET | `/ingredient/list` | 无需认证 | 获取食材列表 |
| GET | `/ingredient/detail/{id}` | 无需认证 | 获取食材详情 |
| GET | `/ingredient/category/{category}` | 无需认证 | 按分类获取食材 |
| GET | `/ingredient/search?keyword=鸡` | 无需认证 | 搜索食材 |
| POST | `/ingredient/save` | 管理员 | 新增食材 |
| PUT | `/ingredient/update` | 管理员 | 更新食材 |
| DELETE | `/ingredient/delete/{id}` | 管理员 | 删除食材 |
| POST | `/ingredient/nutrition` | 无需认证 | 计算食材营养 |
| POST | `/ingredient/substitute` | 无需认证 | 获取食材替代建议 |

## 11. 健康文章

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| GET | `/article/list` | 可选用户 | 分页获取文章 |
| GET | `/article/tags` | 无需认证 | 获取文章标签 |
| GET | `/article/detail/{articleId}` | 可选用户 | 获取文章详情 |
| GET | `/article/recommend` | 可选用户 | 获取推荐文章 |
| GET | `/article/read/history` | 用户 | 获取阅读历史 |
| POST | `/article/read/{articleId}` | 用户 | 记录阅读行为 |
| GET | `/article/search` | 无需认证 | 搜索文章 |
| POST | `/article/like/{articleId}` | 用户 | 点赞文章 |
| DELETE | `/article/like/{articleId}` | 用户 | 取消点赞 |
| GET | `/article/like/status/{articleId}` | 用户 | 查询点赞状态 |
| POST | `/article/collect/{articleId}` | 用户 | 收藏文章 |
| DELETE | `/article/collect/{articleId}` | 用户 | 取消收藏 |
| GET | `/article/collect/status/{articleId}` | 用户 | 查询收藏状态 |
| GET | `/article/collect/list` | 用户 | 获取收藏列表 |
| GET | `/article/comment/list/{articleId}` | 无需认证 | 获取评论树 |
| POST | `/article/comment/{articleId}` | 用户 | 发表评论或回复 |
| DELETE | `/article/comment/{commentId}` | 评论作者或管理员 | 删除评论 |
| POST | `/article/publish` | 用户 | 发布文章 |
| POST | `/article/save` | 管理员 | 保存文章 |
| PUT | `/article/update` | 管理员 | 更新文章 |
| DELETE | `/article/delete/{articleId}` | 管理员 | 删除文章 |
| GET | `/article/admin/collect-stats` | 管理员 | 获取收藏热度 |

## 12. AI 助手

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| GET | `/assistant/conversations` | 用户 | 获取会话列表 |
| POST | `/assistant/conversations` | 用户 | 创建会话 |
| GET | `/assistant/conversations/{conversationId}/messages` | 用户 | 获取会话消息 |
| POST | `/assistant/chat` | 用户 | 发送聊天消息 |
| DELETE | `/assistant/conversations/{conversationId}` | 用户 | 删除会话 |

### 12.1 聊天

`POST /assistant/chat`

请求体：

```json
{
  "conversationId": 12,
  "rawPrompt": "早餐吃什么比较健康",
  "prompt": "早餐吃什么比较健康"
}
```

成功响应 `data` 包含 `conversationId`、`conversation`、`userMessage`、`assistantMessage` 等字段。

## 13. 通知

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| GET | `/notification/list` | 用户 | 获取通知列表 |
| PUT | `/notification/read/{id}` | 用户 | 标记已读 |
| PUT | `/notification/delete/{id}` | 用户 | 软删除通知 |
| POST | `/notification/admin/publish` | 管理员 | 发布通知 |

### 13.1 管理员发布通知

`POST /notification/admin/publish`

请求体：

```json
{
  "title": "系统通知",
  "content": "这是一条系统通知",
  "type": "system",
  "userId": null
}
```

`userId` 为空时向所有启用用户发布，否则向指定用户发布。

## 14. 后台管理总览

### 14.1 总览

`GET /admin/overview`

认证：管理员

成功响应 `data` 包含：

- `summary`：用户、食材、食谱、文章、通知等汇总
- `trends`：趋势数据
- `topRecipes`：热门食谱
- `topArticles`：热门文章
- `recentActivities`：最近活动
- `meta`：统计说明和日期

## 15. 联调建议

1. 登录后从 `data.token` 中获取 JWT，并写入后续请求头。
2. 前端和后端统一使用 `code=200` 判断成功，不要只判断 HTTP 200。
3. 推荐类接口依赖算法服务，联调前确保 Flask 服务 `localhost:5000` 已启动。
4. 管理员接口由 Spring Security 根据 `ROLE_ADMIN` 控制，普通用户会返回 403 或业务 400。
5. 移动端 `app/utils/request.js` 使用 LAN IP，真机联调前需要检查 IP 和防火墙。
