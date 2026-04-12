# AI 小助手聊天记录数据库存储方案

## 一、设计目标

当前 AI 小助手模块的聊天记录仅保存在前端 localStorage 中。为了支持用户刷新页面、重新登录、跨设备查看历史记录，并提升系统完整度，建议将聊天记录迁移到 MySQL 中保存。

目标是实现：

- 聊天记录保存在数据库
- 用户重新登录后可恢复历史聊天
- 支持按会话查看历史消息
- 为后续扩展多会话、搜索、统计、后台分析打基础

---

## 二、推荐的数据结构设计

建议使用两张表：

1. `assistant_conversation`：保存聊天会话
2. `assistant_message`：保存会话中的消息

这种设计便于扩展，也更符合常见聊天系统的数据建模方式。

---

## 三、会话表 assistant_conversation

### 作用
表示一次聊天会话，例如：
- 减脂期鸡胸肉替代
- 乳糖不耐受饮食建议
- 晚餐搭配建议

### 建议字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| user_id | bigint | 用户 ID |
| title | varchar(100) | 会话标题 |
| summary | varchar(255) | 会话摘要，可选 |
| message_count | int | 消息总数 |
| last_message_at | datetime | 最后一条消息时间 |
| is_deleted | tinyint | 是否删除 |
| create_time | datetime | 创建时间 |
| update_time | datetime | 更新时间 |

### 建议建表 SQL

```sql
CREATE TABLE assistant_conversation (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    title VARCHAR(100) NOT NULL,
    summary VARCHAR(255) DEFAULT NULL,
    message_count INT DEFAULT 0,
    last_message_at DATETIME DEFAULT NULL,
    is_deleted TINYINT DEFAULT 0,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

---

## 四、消息表 assistant_message

### 作用
保存一段会话中的每条消息。

### 建议字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| conversation_id | bigint | 所属会话 ID |
| user_id | bigint | 用户 ID，便于查询 |
| role | varchar(20) | user / assistant / context |
| content | text | 文本内容 |
| cards_json | text | 卡片内容 JSON |
| message_type | varchar(20) | text / cards / context |
| create_time | datetime | 创建时间 |

### 建议建表 SQL

```sql
CREATE TABLE assistant_message (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    conversation_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT,
    cards_json TEXT,
    message_type VARCHAR(20) DEFAULT 'text',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 五、为什么这样设计

### 1. 会话和消息分离，便于扩展
后续可支持：
- 左侧历史会话列表
- 搜索历史会话
- 会话重命名
- 会话删除
- 管理员统计 AI 使用情况

### 2. 能兼容当前前端消息结构
当前前端消息对象已经包含：
- `role`
- `text`
- `cards`

与数据库结构可以自然映射。

### 3. context 消息也可保留
当前前端会把“发给 AI 的上下文摘要”作为一条 `context` 消息插入到消息流中。数据库也可以保存这类消息，便于后续调试和展示。

---

## 六、后端代码结构建议

结合当前项目后端结构，建议新增以下内容。

### 1. Entity
新增：
- `backend/src/main/java/com/health/entity/AssistantConversation.java`
- `backend/src/main/java/com/health/entity/AssistantMessage.java`

### 2. Mapper
新增：
- `backend/src/main/java/com/health/mapper/AssistantConversationMapper.java`
- `backend/src/main/java/com/health/mapper/AssistantMessageMapper.java`

建议继续沿用当前项目中 `BaseMapper<T>` 的风格。

### 3. Service
新增：
- `backend/src/main/java/com/health/service/AssistantChatService.java`
- `backend/src/main/java/com/health/service/impl/AssistantChatServiceImpl.java`

Service 主要负责：
- 创建会话
- 获取会话列表
- 获取消息列表
- 保存 user message
- 调用现有 AI 食材替代逻辑
- 保存 assistant message
- 更新会话摘要和时间
- 删除会话

### 4. Controller
新增：
- `backend/src/main/java/com/health/controller/AssistantChatController.java`

建议统一挂载在：
- `/assistant`

---

## 七、推荐接口设计

### 1. 获取当前用户会话列表
**接口：**
`GET /api/assistant/conversations`

**作用：**
获取当前登录用户的历史会话列表。

**返回示例：**
```json
{
  "code": 200,
  "message": "获取会话列表成功",
  "data": [
    {
      "id": 1,
      "title": "减脂期鸡胸肉可以替换成什么？",
      "summary": "讨论减脂期高蛋白替代方案",
      "messageCount": 6,
      "lastMessageAt": "2026-04-12 14:30:00"
    }
  ]
}
```

---

### 2. 创建新会话
**接口：**
`POST /api/assistant/conversations`

**请求体：**
```json
{
  "title": "减脂期鸡胸肉可以替换成什么？"
}
```

**说明：**
如果前端未传标题，也可以由后端根据第一句用户问题自动生成。

---

### 3. 获取某个会话的消息列表
**接口：**
`GET /api/assistant/conversations/{conversationId}/messages`

**返回示例：**
```json
{
  "code": 200,
  "message": "获取消息成功",
  "data": [
    {
      "id": 11,
      "role": "user",
      "text": "减脂期鸡胸肉可以替换成什么？",
      "cards": null,
      "messageType": "text",
      "createTime": "2026-04-12 14:28:00"
    },
    {
      "id": 12,
      "role": "assistant",
      "text": "",
      "cards": [
        {
          "name": "虾仁",
          "similarity": "高蛋白低脂",
          "nutrition_difference": "脂肪更低",
          "usage_suggestion": "适合清炒或水煮"
        }
      ],
      "messageType": "cards",
      "createTime": "2026-04-12 14:28:03"
    }
  ]
}
```

---

### 4. 发送消息
**接口：**
`POST /api/assistant/chat`

**请求体建议：**
```json
{
  "conversationId": 1,
  "rawPrompt": "减脂期鸡胸肉可以替换成什么？",
  "prompt": "请结合以下用户信息回答食材替代问题......",
  "healthInfo": {},
  "dietGoal": {}
}
```

**后端流程建议：**
1. 校验用户登录
2. 校验会话是否属于当前用户
3. 保存 user 消息
4. 保存 context 消息（可选）
5. 调用现有 `RecipeServiceImpl.getIngredientSubstitutes(...)`
6. 保存 assistant 消息
7. 更新会话表中的：
   - `message_count`
   - `last_message_at`
   - `summary`
   - `update_time`
8. 返回 assistant 消息给前端

**优势：**
前端只需发起一次请求，后端同时完成“生成建议 + 持久化聊天记录”。

---

## 八、如何复用当前已有逻辑

当前已有链路为：
- `IngredientSubstitute.vue` 组织 prompt
- `recipeApi.getSubstitutes(...)`
- 后端推荐接口
- `RecipeServiceImpl.getIngredientSubstitutes(...)`

建议不要重写 AI 逻辑，而是在新的 `AssistantChatService` 中直接复用：
- `RecipeService.getIngredientSubstitutes(...)`

这样可以实现：
- AI 生成逻辑继续放在 `RecipeServiceImpl`
- 聊天记录持久化放在 `AssistantChatService`

职责更清晰，也更容易维护。

---

## 九、前端改造建议

### 1. 新增状态
前端建议新增：
- `conversationList`
- `currentConversationId`

### 2. 页面初始化流程
进入 AI 小助手页面时：
1. 请求会话列表
2. 默认打开最近一条会话
3. 请求该会话消息列表
4. 渲染到 `messages`

### 3. 点击“新建会话”
1. 调用创建会话接口
2. 更新会话列表
3. 清空当前消息区
4. 切换到新会话

### 4. 发送消息
1. 前端调用 `/assistant/chat`
2. 后端存储 user/assistant 消息
3. 前端将返回结果更新到 `messages`
4. 刷新左侧会话摘要和时间

---

## 十、建议新增前端 API 文件

建议新增：
- `frontend/src/api/assistant.js`

示例结构：
```js
import axios from '../utils/axios';

export default {
  getConversations() {
    return axios.get('/assistant/conversations');
  },
  createConversation(payload) {
    return axios.post('/assistant/conversations', payload);
  },
  getMessages(conversationId) {
    return axios.get(`/assistant/conversations/${conversationId}/messages`);
  },
  chat(payload) {
    return axios.post('/assistant/chat', payload, { timeout: 60000 });
  },
  deleteConversation(id) {
    return axios.delete(`/assistant/conversations/${id}`);
  }
};
```

这样能避免继续把 AI 聊天接口混在 `recipe.js` 中，结构会更清楚。

---


