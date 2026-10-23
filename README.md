# 健康饮食推荐系统启动指南

## 系统架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   前端 (Vue)    │────▶│  后端 (Spring)  │────▶│  算法服务       │
│  localhost:5173 │     │  localhost:8080 │     │  localhost:5000 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         │                      MySQL                   │
         │                 localhost:3306               │
         └──────────────────────────────────────────────┘
```

## 启动顺序

### 1. 启动数据库 (MySQL)
确保 MySQL 服务已启动，默认端口 3306。

开发库 `health_diet` 用 `database/health_diet.sql` 手工导入（全量数据，含示例账号）。

**跑接口自动化时不要用开发库**，单独建测试库：

```bash
database\rebuild_test_db.bat
# 等价于：python database/init_test_db.py --db health_diet_test
```

脚本会建 `health_diet_test`、导入 `schema.sql`（表结构）和 `seed_test.sql`
（两个测试账号 + 食材数据），并拒绝清空开发库 `health_diet`。
启动后端时指定同一个库：`set DB_NAME=health_diet_test`。

### 2. 启动算法服务 (Python Flask)
```bash
cd algorithm
pip install -r requirements.txt
python app.py
```
- 服务地址: http://localhost:5000
- 提供的 API:
  - `/api/recommend/recipes` - 智能食谱推荐
  - `/api/recommend/substitute` - 食材替代建议
  - `/api/analyze/health` - 健康数据分析
  - `/api/recommend/articles` - 个性化文章推荐

### 3. 启动后端服务 (Spring Boot)
```bash
cd backend
mvn clean package -DskipTests
java -jar target/health-diet-backend-1.0-SNAPSHOT.jar
```
- 服务地址: http://localhost:8080/api

### 4. 启动前端服务 (Vue)
```bash
cd frontend
npm install
npm run dev
```
- 服务地址: http://localhost:5173

## 功能对应关系

| 前端功能 | 后端API | 算法服务API |
|---------|---------|------------|
| 食谱推荐 | `/api/recommend/recipes` | `/api/recommend/recipes` |
| 食材替代 | `/api/recommend/ingredient/substitute` | `/api/recommend/substitute` |
| 健康分析 | `/api/health/analyze` | `/api/analyze/health` |
| 文章推荐 | `/api/article/recommend` | `/api/recommend/articles` |

## 快速启动脚本

在 Windows 上可以使用以下脚本一键启动：
1. `database/rebuild_test_db.bat` - 重建自动化测试库（`health_diet_test`，不会动开发库）
2. `algorithm/start_algorithm.bat` - 启动算法服务
3. 后端通过 IDE 或命令行启动
4. 前端 `npm run dev`

## 常见问题

### 1. 算法服务连接失败
检查：
- Python 环境是否安装了依赖: `pip install flask flask-cors pandas numpy`
- 端口 5000 是否被占用

### 2. 后端调用算法服务失败
检查：
- 算法服务是否已启动
- 后端 application.yml 中的 algorithm.base-url 配置

### 3. 前端跨域问题
已通过 Vite 代理解决，前端请求 `/api/*` 会转发到后端
