# Java 读代码 · 知识点手册

> 建立于 2026-11-05 · 目标：读懂 Spring Boot 项目代码（不是会写后端）
>
> **用法**
> ① 每讲一个点，追加一条，编号递增
> ② 复习时**只看「人话解答」+「关键代码」**，两栏扫完就算过
> ③ 每节末尾的自测题，先自己答，再对答案
> ④ 每条都标了「它出现在哪」，可以直接打开对应文件对照

---

## 起点诊断（2026-11-05）

用 `AuthController.java` 的真实代码问了三个问题，三题都答不上来。结论：**不是缺三个知识点，是缺同一个底层概念**（对象是谁创建的），补完 01 后第 1、3 题会一起通。

| 问题 | 实际在考什么 | 状态 |
|---|---|---|
| `userService` 谁给它赋的值？ | IoC 容器 / 依赖注入 | → 见 **01** |
| 前端 JSON 怎么变成 `UserRegisterDTO` 的？ | Spring MVC 参数绑定 | 待补（02） |
| `UserService` 是接口，怎么找到实现类的？ | 按类型查找 Bean | → 见 **01 延伸** |

---

## 索引

| # | 知识点 | 一句话 |
|---|---|---|
| 00 | 整体三层架构 | Controller 接客、Service 干活、Mapper 取数，只能自上而下调 |
| 00B | 教材切换：student-core-system 全景 | 14 文件 / 916 行，三层齐全但机制少一半，可全读完 |
| 01 | `@Autowired` 的变量谁赋的值 | 容器启动时创建好对象，按类型塞进变量 |
| 02 | Mapper 为什么几乎是空的 | `extends BaseMapper<X>` 自带十几个 CRUD，通用的不用写 |

---

## 00 · 整体框架：三层架构与调用方向

**人话解答**

Java 后端标准叫法是**三层架构**（也叫表现层 / 业务层 / 持久层）：

| 层 | 目录 | 数量 | 管什么 | 不该管什么 |
|---|---|---|---|---|
| Controller | `controller/` | 11 | 接请求、校验参数、拼响应 | 不写业务判断、不碰 SQL |
| Service | `service/` + `service/impl/` | 9 + 8 | 业务逻辑、事务边界 | 不关心 HTTP、不关心 JSON |
| Mapper | `mapper/` | 19 | 取数 / 存数 | 不写业务判断 |

MySQL 不算一层（它是数据库，不是代码）。

**餐厅类比**：Controller = 服务员（接单上菜），Service = 厨师（做菜），Mapper = 仓库（取食材）。服务员不做菜，厨师不迎客，仓库不管客人点了什么。

**层与层只靠两个机制连接**

| 机制 | 代码长相 | 作用 |
|---|---|---|
| **注入** | `@Autowired private UserService userService;` | 拿到下一层对象（见 01） |
| **实现** | `public class UserServiceImpl implements UserService` | 接口只有签名，这个类填实现 |

⭐ 关键：Controller 里声明的类型是**接口** `UserService`，运行时塞进来的是 **`UserServiceImpl` 的对象**。所以调 `userService.login()` 实际执行的是 Impl 里的代码。这就是每个业务都有两个文件的原因——**换实现不用改调用方**（测试时换 Mock，Controller 一行不动）。

**一次请求的完整路径（登录，可照着读）**

```
POST /api/auth/login
  ↓ security/JwtAuthorizationFilter.java      门禁，每个请求先过
  ↓ controller/AuthController.java:62          @PostMapping("/login")
  ↓   @RequestBody  JSON → UserLoginDTO
  ↓   @Valid        触发 DTO 字段校验
  ↓ service/UserServiceImpl.java               userService.login(dto) ← 真正干活
  ↓ mapper/UserMapper.java                     selectByEmail(...)
  ↓   @Select 里的 SQL 执行
  ↓ entity/User.java                           一行表记录 → 一个对象
  ↓ ResponseEntity<Map> → JSON
  ↓ 中途异常 → config/GlobalExceptionHandler 统一兜底
```

**Entity 和 DTO 为什么不能合并**

| | `entity/`（19 个） | `dto/`（5 个） |
|---|---|---|
| 对应 | 一张数据库表 | 一次请求的参数 |
| 字段 | 表结构（含 id、创建时间、密码密文） | 前端实际发来的字段 |
| 谁用 | Mapper | Controller |

前端不能直接往「表」里写：注册时传的是明文密码、表里存的是密文；表里有 `create_time` 但前端不该传。DTO 是隔离带。
**点菜单（DTO）上只有“宫保鸡丁”，不会有食材编号、库存、进价——那是台账（Entity）的事。**

**改需求动哪几个文件（导航表）**

| 要做什么 | 动几处 | 具体 |
|---|---|---|
| 加一个新接口 | 4 | Controller + Service 接口 + Impl + Mapper |
| 改业务规则（如密码策略） | 1 | 只改 Impl |
| 改 SQL / 加查询条件 | 1 | 只改 Mapper |
| 表加字段 | 3–4 | Entity + DTO + Mapper + 前端 |
| 改返回格式 | 1 | Controller |

**读代码的顺序：顺着调用方向，不顺着目录**

1. `controller/AuthController.java`（82 行，看有哪些入口）
2. `service/UserService.java`（只有方法名，是能力清单）
3. `service/impl/UserServiceImpl.java`
4. `mapper/UserMapper.java`

反过来读（先看 Mapper）会不知道 SQL 是给谁用的。

---

## 00B · 教材切换：`student-core-system` 全景图

**换教材的原因（2026-11-05 决定）**

| | healthy（原教材） | student-core-system（现教材） |
|---|---|---|
| 位置 | `D:/jiankang/healthy/backend` | `C:/Users/user/Desktop/Java EE/实验/student-core-system` |
| 规模 | 76 文件 / 12264 行 | **14 文件 / 916 行** |
| 能不能全读完 | 不能，只能挑着读 | **能，两小时够** |
| 数据库 | MySQL + MyBatis-Plus | 无，数据在内存 `ArrayList` 里 |
| Service 结构 | 接口 + Impl 两个文件 | 只有一个类，没有接口 |
| 依赖注入 | `@Autowired` 字段注入（70 处） | **构造器注入，一个 `@Autowired` 都没有** |
| 技术栈 | Spring Boot 2 + MyBatis + JWT | Spring Boot 3.2 + Java 21 + Bean Validation |
| 定位 | 简历项目 | 课程实验，**读代码的练习场** |

⭐ 关键判断：**这个项目是「小而全」的标本**——三层、异常、校验、统一响应全都在，但每样只有一份，没有 19 个 Mapper 那种噪音。先把它读穿，再回 healthy 看规模，阻力小得多。

**14 个文件，按 5 组记（不用背文件名，只要知道每组干什么）**

| 组 | 包 | 文件（行数） | 一句话 |
|---|---|---|---|
| 启动 | 根包 | `ScoreQueryApplication`（15） | 唯一的 `main`，`@SpringBootApplication` 扫全包 |
| 接客 | `controller/` | `StudentController`（54）、`ScoreController`（63） | 6 个接口：3 个查、3 个写 |
| 干活 | `service/` | `ScoreService`（127） | 全部业务规则，6 个方法 |
| 取数 | `repository/` | `StudentRepository`（125） | 内存三份数据：学生 / 课程 / 成绩 |
| 数据形状 | `entity/` `dto/` | `Student`、`Course`、`Score`、2 个 DTO | entity 是"库里长什么样"，dto 是"请求带什么" |
| 包装与兜底 | `common/` `exception/` | `ApiResponse`（77）、`ErrorCode`（47）、`BusinessException`（41）、`GlobalExceptionHandler`（124） | 统一返回体、错误码表、业务异常、异常兜底 |

**依赖方向（只有这一个方向，绝不反向）**

```
Controller ──持有──> Service ──持有──> Repository ──持有──> 三个 List / Map
```

Controller 不认识 Repository，Repository 也不认识 Service。想验证：`StudentRepository.java` 的 import 里没有 `service` 也没有 `controller`。

**这个项目比 healthy 少了什么（很重要，别拿旧结论硬套）**

| healthy 里有 | 这里有没有 | 影响 |
|---|---|---|
| MySQL / MyBatis-Plus | ❌ 没有 | 02 讲的 `BaseMapper`、`QueryWrapper` **在这里完全不出现**，别去找 |
| Service 接口 + Impl | ❌ 没有 | 00 里"接口只有签名、运行时是实现类"这条，**这里看不到**——注入的直接就是类本身 |
| `@Autowired` | ❌ 一处都没有 | 01 的结论仍然成立，但**触发方式换了**：靠构造器 |
| JWT / 登录 | ❌ 没有 | 那条登录链路的读法留着，将来读别的项目再用 |
| DTO + Bean Validation | ✅ 有 | `@NotBlank` / `@Min` / `@Max` |
| 全局异常处理 | ✅ 有，而且比 healthy 更清晰 | 自定义 `BusinessException` 带错误码 |

**读代码的顺序（6 步，按这个走不会晕）**

1. `pom.xml` — 看依赖，先知道"这个项目有什么能力"（没有 jdbc / jpa 就知道不连库）
2. `ScoreQueryApplication` — 15 行，看包名和启动方式
3. `controller/StudentController` — 看有哪些入口、路径长什么样
4. `service/ScoreService` — 主线，6 个方法就是 6 条业务
5. `repository/StudentRepository` — 数据从哪来（这里会看到 `initStudents()` 硬编码 5 个学生）
6. `exception/` + `common/` — 最后看包装和兜底，因为它们是被调用方

**对照原来的手册：哪些还成立**

| 原知识点 | 在本项目里 |
|---|---|
| 00 三层架构 + 调用方向 | ✅ 完整成立，且更清楚（没有 Impl 干扰） |
| 01 「谁 new 的对象」 | ✅ 成立，但入口从 `@Autowired` 换成**构造器** |
| 02 Mapper 为什么空的 | ⚠️ 用不上（本项目没有 ORM），保留作 healthy 项目的知识 |

**自测题**

`ScoreService` 里写的是：

```java
private final StudentRepository studentRepository;

public ScoreService(StudentRepository studentRepository) {
    this.studentRepository = studentRepository;
}
```

全文没有 `@Autowired`，为什么 `studentRepository` 不是 null？

- A. 因为 `final` 会强制 Spring 赋值
- B. Spring 发现这个类只有一个构造器，就自动调用它，并且把容器里的 `StudentRepository` 对象当参数传进去
- C. `@Service` 注解会自己 `new` 一个 Repository 塞进去

**答案见文末「答案区」**

---

## 01 · `@Autowired` 的变量，谁给它赋的值

**原话疑问**（2026-11-05）

> `@Autowired private UserService userService;` 这个变量谁给它赋的值？代码里找不到 `new UserService()`。

**人话解答**

先看你已经会的写法：

```java
UserService userService = new UserServiceImpl();   // ① 造对象
userService.register(dto);                        // ② 用对象
```

「先 new 再造，再造完才用」——这条规则你已经有了。

项目里却是这样：

```java
@Autowired
private UserService userService;   // 只声明，没有 new
```

按规则推：没 new → 没赋值 → 值为 `null` → 调用方法应该抛空指针。**但服务明明跑得好好的。**

原因：**Spring 在启动的那几秒里，替你 new 了。**

启动时它做三件事：

1. **扫描**：找出所有带 `@Service` / `@Controller` / `@Repository` / `@Component` 的类
2. **创建**：给每个类 `new` 一个对象，放进一个池子里
3. **注入**：遇到 `@Autowired`，从池子里取出**类型匹配**的那个对象，赋给变量

所以 `@Autowired` 真正说的是：**「这个变量我不负责创建，你从池子里拿一个给我。」**

三个必须记住的词：

| 词 | 指什么 | 类比 |
|---|---|---|
| **IoC 容器** | 那个装对象的池子 | 公司的 IT 仓库 |
| **Bean** | 被放进池子里的对象 | 仓库里的一台电脑 |
| **依赖注入（DI）** | 「从池子取出来塞进变量」这个动作 | 入职时电脑已配到你桌上 |

用入职类比一遍：**你不会自己买电脑（不 new），IT 在你到岗前就配好了（启动时创建），你坐下就能用（注入完成）。如果漏了你这台，你就只能干坐着——那就是空指针。**

**它出现在哪**

`controller/AuthController.java:25-26`，以及全项目 **70 处** `@Autowired`。

**延伸：为什么接口能直接调用？**

`UserService` 是接口（`service/UserService.java`），里面只有方法签名没有实现。但 `userService.login(...)` 能跑，是因为：

容器里存的是 **`UserServiceImpl` 的实例**（它 `implements UserService`），Spring 按**类型**匹配时，把实现类的对象注给了接口类型的变量。

这就是为什么项目里每个 Service 都有「接口 + Impl」两个文件：**换实现不用改调用方**。测试时你把 Impl 换成 Mock，Controller 一行都不用动——这正是你在 Python 里做 mock 的那件事，Java 是在语言层面用接口做的。

**自测题**

把 `@Autowired` 删掉，保留 `private UserService userService;`，仍然调用 `userService.register(dto)`，会发生什么？

- A. 编译报错，因为没 new
- B. 能编译通过，运行时抛空指针
- C. 正常运行，Spring 会自动补上

**答案：B**

- **A 不对**：Java 里**成员变量**不初始化是合法的，默认值就是 `null`，编译不报错。只有**方法里的局部变量**才强制要求初始化。这是个容易混的点。
- **C 不对**：Spring 只认 `@Autowired` / `@Resource` 这类注解。没有注解，它根本不知道你需要注入，那个变量就一直有空。

---

## 02 · Mapper 为什么几乎空的

**原话疑问**（2026-11-05）

> `UserMapper.java` 不是几乎空的吗？

**人话解答**

对，而且不止它一个。19 个 Mapper 的实际分布：

| 行数 | 数量 | 内容 |
|---|---|---|
| 7–9 行 | **11 个** | 完全空，只有一句 `extends BaseMapper<X>` |
| 13–16 行 | 4 个 | 加了一两个方法 |
| 27–61 行 | 4 个 | 有自定义 `@Select` |

`UserMapper` 全文 8 行，一行 SQL 都没有：

```java
public interface UserMapper extends BaseMapper<User> {

}
```

**空还能用，是因为 `BaseMapper` 自带十几个通用方法**：`insert` / `deleteById` / `updateById` / `selectById` / `selectList` / `selectCount` / `selectPage` …

⭐ **`<User>` 这个泛型不只是类型标记**，框架靠它知道表名：

```
BaseMapper<User>  ──泛型──>  User 类
                                ↓ @TableName("user")   → 表名
                                ↓ @TableField          → 列名
                                ↓
                        自动生成 SELECT / INSERT / UPDATE / DELETE
```

所以 `entity/` 上那些 `@TableName` / `@TableId` / `@TableField` **不是给人看的，是给框架拼 SQL 用的**。

**那条件查询写在哪？用 `QueryWrapper`**

`UserServiceImpl.java:119` 的真实代码：

```java
public User findByEmail(String email) {
    return userMapper.selectOne(new QueryWrapper<User>().eq("email", email));
}
```

`new QueryWrapper<User>().eq("email", email)` 就等于 SQL 里的 `WHERE email = ?`：

| Java 写法 | 等价 SQL |
|---|---|
| `selectOne(wrapper)` | `SELECT * FROM user WHERE ... LIMIT 1` |
| `eq("email", x)` | `WHERE email = x` |
| `orderByDesc("create_time")` | `ORDER BY create_time DESC` |
| `selectList(wrapper)` | 返回 List |

**所以层次是这样递进的：**

1. `BaseMapper` 给**方法**（增删改查的骨架）
2. `QueryWrapper` 给**条件**（WHERE 部分）
3. `@Select` 只在上面两样都表达不了时才写（多表联查、复杂聚合）

`UserMapper` 空着，说明用户表的操作全落在第 1、2 层就解决了，根本不需要写 SQL。

**读代码的实用规则**

| Mapper 行数 | 怎么办 |
|---|---|
| ≤ 13 行 | **直接跳过**，标准 CRUD，看类名就知道能干什么 |
| ≥ 27 行 | 值得看，有自定义逻辑 |

19 个里只有 4 个需要打开。

**自测题**

`userMapper.selectOne(new QueryWrapper<User>().eq("email", email))` 等价于哪条 SQL？

- A. `SELECT * FROM user`
- B. `SELECT * FROM user WHERE email = ?`
- C. `UPDATE user SET email = ?`

**答案：B**

`selectOne` 表示“只取一条”（等价于加了 `LIMIT 1`），`eq("email", email)` 是 WHERE 条件。A 少了条件会查出全表，C 是更新语句——`selectOne` 不写库。

---

## 答案区

**00B 自测题 → 答案：B**

- **A 不对**：`final` 只是"赋过一次就不能再改"，它管的是**改**，不管**第一次谁赋**。`final` 字段如果谁都没赋值，编译期就报错——所以它能保证"一定有值"，但保不了"值从哪来"。
- **C 不对**：`@Service` 只是给这个类贴个标签，告诉 Spring"启动时把我 new 出来放进池子"。它不会去 new 别的类。
- **B 对**：Spring 定了个规矩——**一个类如果只有一个构造器，就不需要写 `@Autowired`，直接用它**。构造器的参数类型是 `StudentRepository`，Spring 就从池子里找一个这个类型的对象传进去。这叫**构造器注入**。

和 `@Autowired` 字段注入的区别，一句话：**字段注入是"对象先造好，再往字段里塞"；构造器注入是"造的时候就得把材料递进去"**。类比：前者是装修完再搬家具，后者是盖房子时钢筋水泥必须到位。

⭐ 这也是为什么字段都写成 `private final`：**值只能在构造器里定一次，之后谁也改不了**，对象一造出来就是完整可用的状态。

---

## 待补清单

> 教材已换成 `student-core-system`，清单按新项目重排。标「healthy」的两条留到回读原项目时再说。

| # | 知识点 | 触发场景 | 状态 |
|---|---|---|---|
| 03 | `@RestController` / `@GetMapping` / `@PathVariable` 谁把 URL 对到方法的 | 读 `StudentController` 时 | 待讲 |
| 04 | `@RequestBody` + `@Valid` 怎么把 JSON 变成 DTO，校验失败谁抛 | 读 `ScoreController.create` 时 | 待讲 |
| 05 | `BusinessException` 怎么被 `@RestControllerAdvice` 接住 | 读 `GlobalExceptionHandler` 时 | 待讲 |
| 06 | `ApiResponse<T>` 泛型 + `ResponseEntity` 状态码（201/204） | 读 `ScoreController` 时 | 待讲 |
| 07 | `update()` 只 `setScore` 没 `save`，为什么数据真的改了 | 读 `ScoreService.update` 时 | 待讲 |
| 08 | 内存 `List` 做存储的坑（多线程 / 重启丢数据 / 测开的视角） | 读完主线后 | 待讲 |
| 09 | `@Transactional` 加在哪层、为什么 | healthy 项目 | 暂缓 |
| 10 | `@Select` 写在接口上怎么执行 | healthy 项目 | 暂缓 |

