import argparse
import os
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

try:
    import pymysql
except ImportError:  # pragma: no cover - fallback for environments without pymysql
    pymysql = None


@dataclass(frozen=True)
class ArticleGeneratorConfig:
    random_seed: int = 20260426
    article_count: int = 120
    article_id_start: int = 2100001
    output_sql_path: Path = Path("D:/biyesheji/database/generated_articles.sql")
    insert_batch_size: int = 100


CONFIG = ArticleGeneratorConfig()

DEFAULT_AUTHORS: List[str] = ["健康饮食助手", "营养师小林", "营养顾问周老师", "健康管理编辑部"]


ARTICLE_TOPICS: List[Dict[str, object]] = [
    {
        "category": "饮食指南",
        "goal_type": "healthy_weight_gain",
        "suitable_for": "偏瘦人群、训练后恢复人群",
        "tags": ["增重", "高能量", "加餐", "恢复"],
        "title_patterns": [
            "健康增重阶段怎么安排{focus}",
            "想增重不增脂，先学会{focus}",
            "{focus}做对了，增重效率会更稳定",
        ],
        "focuses": ["三餐结构", "加餐策略", "训练后补给", "全天热量分配"],
        "sections": [
            "先保证总热量稳定高于维持水平，再考虑蛋白质和碳水的分配。",
            "把主食、优质蛋白和健康脂肪同时放进一餐，比单纯多吃甜食更容易长期坚持。",
            "加餐最好安排在上午、下午和训练后，避免全部堆到夜间。",
            "记录一周体重变化和饮食执行率，比只看某一天吃得多不多更有意义。",
        ],
        "tips": [
            "可优先选择燕麦、全麦面包、牛奶、酸奶、坚果和鸡蛋做加餐组合。",
            "若食量小，可以把液体热量和半固体食物加进计划，例如酸奶杯、奶昔、燕麦粥。",
            "每周观察体重上升 0.25kg 到 0.5kg，通常更稳妥。",
        ],
    },
    {
        "category": "营养知识",
        "goal_type": "muscle_toning",
        "suitable_for": "健身人群、力量训练人群",
        "tags": ["增肌", "蛋白质", "训练恢复", "力量训练"],
        "title_patterns": [
            "{focus}为什么决定增肌效果",
            "增肌人群最容易忽略的{focus}",
            "训练期把{focus}安排好，恢复会更快",
        ],
        "focuses": ["蛋白质分配", "训练后进食", "碳水安排", "恢复餐"],
        "sections": [
            "增肌不只看蛋白总量，还要看全天是否均匀分配到三餐和加餐中。",
            "训练后及时补充蛋白和碳水，有助于恢复糖原并支持肌肉合成。",
            "长期能量摄入不足时，即使训练强度高，肌肉增长也会受限。",
            "饮食计划应和训练周期配合，休息日也要保留基础蛋白摄入。",
        ],
        "tips": [
            "每餐尽量有明确蛋白来源，例如鸡胸肉、鱼肉、牛肉、鸡蛋或豆制品。",
            "训练前后可搭配主食，避免只补蛋白不补碳水。",
            "用一周为单位看力量和围度变化，比盯当天体重更准确。",
        ],
    },
    {
        "category": "减脂指南",
        "goal_type": "fat_loss",
        "suitable_for": "减脂人群、体重管理人群",
        "tags": ["减脂", "热量控制", "高蛋白", "饮食管理"],
        "title_patterns": [
            "减脂期最该重视的{focus}",
            "{focus}调整好，减脂更容易坚持",
            "别只会少吃，减脂真正关键是{focus}",
        ],
        "focuses": ["热量缺口", "饱腹感设计", "主食选择", "外食控制"],
        "sections": [
            "减脂的核心是长期稳定的小幅热量缺口，而不是极端节食。",
            "提高蛋白质和膳食纤维比例，往往比单纯减少主食更能控制饥饿感。",
            "外食时优先确定蛋白来源和蔬菜，再决定主食份量，更容易避免热量失控。",
            "如果连续多天明显疲劳、暴食或训练状态下降，通常意味着缺口过大。",
        ],
        "tips": [
            "常见稳妥做法是先减少油炸零食、含糖饮料和高油酱料。",
            "减脂期不需要完全不吃主食，关键是份量和搭配。",
            "每周体重下降 0.3kg 到 0.8kg 往往更可持续。",
        ],
    },
    {
        "category": "饮食指南",
        "goal_type": "blood_sugar_control",
        "suitable_for": "控糖人群、餐后血糖波动较大人群",
        "tags": ["控糖", "低GI", "血糖管理", "膳食纤维"],
        "title_patterns": [
            "控糖阶段怎么做好{focus}",
            "{focus}稳住了，餐后血糖更平稳",
            "想把控糖做细，先从{focus}开始",
        ],
        "focuses": ["主食替换", "餐盘结构", "加餐安排", "早餐设计"],
        "sections": [
            "控糖的重点不是完全不吃碳水，而是控制总量、来源和进食顺序。",
            "同样一餐里，增加蔬菜、蛋白和豆类，通常能帮助延缓血糖上升。",
            "主食更换成糙米、燕麦、杂豆、藜麦等，只是第一步，份量依然重要。",
            "如果经常空腹过久后再暴食，即使食材看起来健康，也容易让血糖波动加大。",
        ],
        "tips": [
            "先吃蔬菜和蛋白，再吃主食，是很实用的日常策略。",
            "注意饮品和零食中的隐藏糖分，不要只盯正餐。",
            "餐后适度步行，往往比额外节食更容易坚持。",
        ],
    },
    {
        "category": "饮食指南",
        "goal_type": "lipid_control",
        "suitable_for": "控脂人群、血脂偏高人群",
        "tags": ["控脂", "低脂", "心血管", "烹饪方式"],
        "title_patterns": [
            "血脂管理期应该怎么做{focus}",
            "{focus}选对了，控脂会轻松很多",
            "控脂饮食先把{focus}理顺",
        ],
        "focuses": ["烹饪方式", "脂肪来源", "外卖选择", "蛋白替换"],
        "sections": [
            "控脂不只是少吃油，还要减少高饱和脂肪和反式脂肪的来源。",
            "鱼类、豆制品和瘦肉比肥肉、油炸肉制品更适合作为日常蛋白来源。",
            "同样的食材，蒸、炖、煮和少油煎炒，通常比裹粉油炸更有利于血脂管理。",
            "如果长期主食过少、脂肪过高，也不利于整体代谢状态的稳定。",
        ],
        "tips": [
            "先从减少奶茶、炸鸡、奶油点心和高油火锅蘸料开始，性价比最高。",
            "购物时关注配料表和脂肪含量，比只看宣传语更靠谱。",
            "每周安排 2 到 3 次鱼类，有助于提升饮食质量。",
        ],
    },
    {
        "category": "饮食指南",
        "goal_type": "low_sodium",
        "suitable_for": "高血压人群、低盐饮食人群",
        "tags": ["低盐", "高血压", "清淡饮食", "钠摄入"],
        "title_patterns": [
            "低盐饮食最容易忽略的{focus}",
            "{focus}控制住了，低盐更容易落地",
            "做低盐饮食，先从{focus}下手",
        ],
        "focuses": ["隐藏钠来源", "调味替换", "外食点单", "汤类摄入"],
        "sections": [
            "低盐饮食真正难的地方，往往不是做饭时少放盐，而是忽略了酱料、腌制品和加工食品。",
            "火腿、腊味、方便食品、卤味和部分蘸料，钠含量通常远高于想象。",
            "用葱姜蒜、醋、胡椒、柠檬汁和天然香草提味，可以减少对重口调味的依赖。",
            "很多人觉得喝汤清淡，但如果汤底重盐，同样会带来较高钠负担。",
        ],
        "tips": [
            "外食时可主动备注少盐、少酱和酱料分开。",
            "购买预包装食品时优先看钠含量，而不是只看热量。",
            "逐步减盐通常比突然完全清淡更容易长期坚持。",
        ],
    },
    {
        "category": "营养知识",
        "goal_type": "senior_wellness",
        "suitable_for": "老年人群、消化功能较弱人群",
        "tags": ["老年营养", "易消化", "养生", "蛋白补充"],
        "title_patterns": [
            "老年饮食里最重要的{focus}",
            "{focus}安排合理，老年营养更稳",
            "老年人群做好{focus}，吃得舒服也更均衡",
        ],
        "focuses": ["软烂饮食", "蛋白补充", "少量多餐", "早餐质量"],
        "sections": [
            "老年饮食的重点不是吃得越少越清淡，而是在容易消化的前提下保证营养密度。",
            "优质蛋白、足够饮水和规律进餐，对维持体力和恢复能力都很重要。",
            "如果咀嚼和消化能力下降，可以把食材做得更软烂，但不要因此长期只吃单一食物。",
            "少量多餐对部分胃口下降的人更友好，但每餐仍然需要明确的蛋白和主食来源。",
        ],
        "tips": [
            "可以多用蒸、炖、煮、焖等方式，减少过硬和过油的食物。",
            "豆腐、鸡蛋、鱼肉、南瓜、小米、山药都适合作为基础搭配。",
            "定期观察体重、食欲和活动量，有助于及时调整饮食计划。",
        ],
    },
    {
        "category": "营养知识",
        "goal_type": "weight_maintenance",
        "suitable_for": "日常健康管理人群、办公室人群",
        "tags": ["均衡饮食", "早餐", "日常健康", "生活方式"],
        "title_patterns": [
            "日常饮食中最值得优化的{focus}",
            "{focus}做好了，体重维持会更轻松",
            "普通上班族先把{focus}调整好",
        ],
        "focuses": ["早餐质量", "工作日午餐", "晚餐时间", "零食替换"],
        "sections": [
            "体重维持最常见的问题不是大吃大喝，而是工作日饮食节奏混乱和长期久坐。",
            "如果早餐和午餐质量太低，往往会导致下午和夜间更容易出现补偿性进食。",
            "把便利但营养密度低的零食逐步替换掉，通常比突然严格限制更容易坚持。",
            "稳定作息、规律饮水和基础运动，会显著放大饮食调整的效果。",
        ],
        "tips": [
            "一份更稳的早餐通常包含主食、蛋白和水果或蔬菜。",
            "工作日午餐尽量避免只有面点或只有奶茶加零食的组合。",
            "把坚果、酸奶和水果作为备用加餐，能减少高热量临时选择。",
        ],
    },
    {
        "category": "饮食误区",
        "goal_type": "weight_maintenance",
        "suitable_for": "所有人群",
        "tags": ["误区", "饮食管理", "健康习惯", "科普"],
        "title_patterns": [
            "很多人都误会了：{focus}",
            "关于{focus}，最常见的三个误区",
            "{focus}并不是你以为的那样",
        ],
        "focuses": ["不吃主食", "水果代餐", "低脂等于健康", "出汗等于减脂"],
        "sections": [
            "饮食误区的问题在于看起来简单有效，但长期执行后常常会带来更大的反弹和营养失衡。",
            "把某类食物完全妖魔化，通常不利于建立稳定可持续的饮食结构。",
            "真正有效的方法往往没有那么极端，而是更强调份量、搭配和执行稳定性。",
            "如果一种方法只能短期咬牙坚持，通常就不适合作为长期策略。",
        ],
        "tips": [
            "优先问自己这套做法能否执行三个月，而不是只看三天效果。",
            "看到极端承诺时，先回到总热量、营养结构和生活习惯三个基本面。",
            "想改善体重和健康，规律通常比技巧更重要。",
        ],
    },
    {
        "category": "饮食指南",
        "goal_type": "muscle_toning",
        "suitable_for": "训练后恢复人群、运动爱好者",
        "tags": ["训练后饮食", "恢复", "蛋白质", "碳水"],
        "title_patterns": [
            "训练后怎么安排{focus}",
            "{focus}做对了，恢复和表现都会更稳",
            "运动后别乱吃，先搞清楚{focus}",
        ],
        "focuses": ["恢复餐", "碳水补充", "蛋白搭配", "进食时间"],
        "sections": [
            "训练后饮食的目标，不只是填饱肚子，而是帮助恢复、补充糖原并稳定后续食欲。",
            "高强度训练后如果长期不补充碳水，恢复速度和训练表现通常都会受到影响。",
            "恢复餐不一定复杂，关键是主食和蛋白来源明确且容易执行。",
            "训练日总摄入不足时，单靠补剂很难弥补长期饮食结构的问题。",
        ],
        "tips": [
            "常见恢复餐组合包括米饭加鸡胸肉、面包加酸奶、燕麦加牛奶和鸡蛋。",
            "如果当下胃口一般，可以先从液体或半固体食物入手。",
            "训练后 1 小时内吃到一顿结构完整的餐，通常更容易形成稳定习惯。",
        ],
    },
]


def load_author_pool() -> List[str]:
    if pymysql is None:
        return list(DEFAULT_AUTHORS)

    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = int(os.getenv("DB_PORT", "3306"))
    db_username = os.getenv("DB_USERNAME", "root")
    db_password = os.getenv("DB_PASSWORD", "123456")
    db_name = os.getenv("DB_NAME", "health_diet")

    try:
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_username,
            password=db_password,
            database=db_name,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
    except Exception:
        return list(DEFAULT_AUTHORS)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT username, role
                FROM user
                WHERE COALESCE(status, 1) = 1
                  AND username IS NOT NULL
                  AND TRIM(username) <> ''
                ORDER BY CASE WHEN role = 'admin' THEN 0 ELSE 1 END, id ASC
                """
            )
            records = cursor.fetchall()
    except Exception:
        return list(DEFAULT_AUTHORS)
    finally:
        connection.close()

    author_pool: List[str] = []
    seen = set()
    for record in records:
        username = str(record.get("username", "")).strip()
        if not username or username in seen:
            continue
        seen.add(username)
        weight = 3 if record.get("role") == "admin" else 1
        author_pool.extend([username] * weight)

    return author_pool or list(DEFAULT_AUTHORS)


def build_article_rows(
    config: ArticleGeneratorConfig, rng: random.Random, author_pool: List[str]
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    base_date = datetime(2026, 1, 1, 9, 0, 0)

    for index in range(config.article_count):
        topic = ARTICLE_TOPICS[index % len(ARTICLE_TOPICS)]
        article_id = config.article_id_start + index
        focus = rng.choice(topic["focuses"])
        title = rng.choice(topic["title_patterns"]).format(focus=focus)
        content = build_article_content(topic, focus, rng)
        summary = build_summary(content)
        create_time = base_date + timedelta(days=index % 110, minutes=(index * 17) % 1440)
        publish_date = create_time.date().isoformat()
        suitable_for = topic["suitable_for"]
        goal_type = topic["goal_type"]
        read_count = rng.randint(18, 260)
        like_count = rng.randint(2, max(3, read_count // 8))
        comment_count = rng.randint(0, max(2, like_count // 3))

        rows.append(
            {
                "id": article_id,
                "title": title,
                "summary": summary,
                "content": content,
                "category": topic["category"],
                "tags": ",".join(topic["tags"]),
                "author": rng.choice(author_pool or DEFAULT_AUTHORS),
                "suitable_for": suitable_for,
                "goal_type": goal_type,
                "read_count": read_count,
                "like_count": like_count,
                "comment_count": comment_count,
                "publish_date": publish_date,
                "status": 1,
                "create_time": create_time.strftime("%Y-%m-%d %H:%M:%S"),
                "update_time": create_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return rows


def build_article_content(topic: Dict[str, object], focus: str, rng: random.Random) -> str:
    intro = f"{focus}往往决定了一篇饮食建议能不能真正落地。很多人知道方向，但执行一周后就放弃，通常不是因为不努力，而是方法不够具体。"
    body_lines = [intro]
    body_lines.extend(topic["sections"])
    body_lines.append("如果你希望饮食方案真正长期有效，最好同时观察执行便利度、饱腹感、恢复状态和体重变化，而不是只盯某一个数字。")

    chosen_tips = rng.sample(topic["tips"], k=min(3, len(topic["tips"])))
    body_lines.append("可直接执行的建议：")
    body_lines.extend(f"{idx + 1}. {tip}" for idx, tip in enumerate(chosen_tips))
    body_lines.append("最后提醒：同一套饮食方法需要结合作息、活动量和当前目标调整，适合别人的做法未必完全适合自己。")
    return "\n\n".join(body_lines)


def build_summary(content: str) -> str:
    compact = " ".join(content.replace("\n", " ").split())
    return compact[:118] + "..." if len(compact) > 118 else compact


def chunk_rows(rows: List[Dict[str, object]], batch_size: int) -> List[List[Dict[str, object]]]:
    safe_batch_size = max(1, batch_size)
    return [rows[index : index + safe_batch_size] for index in range(0, len(rows), safe_batch_size)]


def sql_value(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{text}'"


def write_article_sql(rows: List[Dict[str, object]], output_path: Path, batch_size: int) -> Path:
    columns = list(rows[0].keys()) if rows else []
    statements: List[str] = [
        "-- Generated health articles",
        "SET NAMES utf8mb4;",
        "",
    ]

    for batch in chunk_rows(rows, batch_size):
        column_sql = ", ".join(f"`{column}`" for column in columns)
        values_sql = ",\n".join(
            f"({', '.join(sql_value(row[column]) for column in columns)})" for row in batch
        )
        statements.append(f"INSERT INTO `health_article` ({column_sql}) VALUES\n{values_sql};")
        statements.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(statements), encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=CONFIG.article_count)
    parser.add_argument("--seed", type=int, default=CONFIG.random_seed)
    parser.add_argument("--start-id", type=int, default=CONFIG.article_id_start)
    parser.add_argument("--batch-size", type=int, default=CONFIG.insert_batch_size)
    parser.add_argument("--output", default=str(CONFIG.output_sql_path))
    args = parser.parse_args()

    config = ArticleGeneratorConfig(
        random_seed=args.seed,
        article_count=args.count,
        article_id_start=args.start_id,
        output_sql_path=Path(args.output),
        insert_batch_size=args.batch_size,
    )
    rng = random.Random(config.random_seed)
    author_pool = load_author_pool()
    rows = build_article_rows(config, rng, author_pool)
    output_path = write_article_sql(rows, config.output_sql_path, config.insert_batch_size)

    print(f"Generated article SQL: {output_path}")
    print(f"health_article: {len(rows)}")
    print(f"authors_loaded: {len(set(author_pool))}")


if __name__ == "__main__":
    main()
