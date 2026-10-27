/* ============================================================
   mock.js · 单一数据源（假数据 / 可后续替换为真实接口）
   数据口径参考《健康饮食推荐系统需求文档 v1.0》
   ============================================================ */
(function () {
  const ASSET = '../assets/';

  const DB = {
    /* ---------------- 当前登录用户 ---------------- */
    user: {
      userId: 1024,
      username: '林嘉禾',
      email: 'jiahe@example.com',
      phone: '138****6021',
      role: 'admin',            // user | admin（体验账号按管理员展示，便于查看后台）
      status: 1,
      joined: '2026-08-12',
      avatarText: '禾'
    },

    /* ---------------- 健康档案 ---------------- */
    health: {
      age: 29,
      gender: '女',
      height: 165,
      weight: 68.4,
      bmi: 25.1,
      bmr: 1396,
      bloodPressure: '128/82',
      bloodSugar: 5.4,
      activity: '轻度活动',
      exerciseMin: 30,
      exerciseType: '快走 / 拉伸',
      chronic: ['高血脂'],
      waist: 78,
      updatedAt: '2026-10-20 09:12'
    },

    /* ---------------- 饮食目标 ---------------- */
    goal: {
      goalType: '减脂',
      startWeight: 71.2,
      currentWeight: 68.4,
      targetWeight: 62.0,
      kcal: 1800,
      proteinPct: 30,
      carbPct: 45,
      fatPct: 25,
      water: 2000,
      meals: 3,
      snack: true,
      startDate: '2026-09-01',
      endDate: '2026-12-31',
      status: 1,
      reminderEnabled: true,
      reminderTime: '07:30'
    },

    /* ---------------- 饮食偏好 ---------------- */
    preferences: {
      dietType: ['清淡', '低脂'],
      allergens: ['花生'],
      dislikes: ['香菜', '动物内脏'],
      likes: ['鸡胸肉', '三文鱼', '蓝莓', '燕麦'],
      mealsPerDay: 3,
      snack: true
    },

    /* ---------------- 食材库 ---------------- */
    ingredients: [
      { id: 1, name: '鸡胸肉', cat: '肉类', kcal: 165, p: 31.0, c: 0, f: 3.6, fiber: 0, sugar: 0, sodium: 74, gi: 0, chol: 85, desc: '高蛋白低脂，减脂期优质蛋白来源', tags: ['高蛋白', '低脂'] },
      { id: 2, name: '三文鱼', cat: '肉类', kcal: 208, p: 20.4, c: 0, f: 13.4, fiber: 0, sugar: 0, sodium: 59, gi: 0, chol: 63, desc: '富含 Omega-3 与优质蛋白', tags: ['优质脂肪', '高蛋白'] },
      { id: 3, name: '牛里脊', cat: '肉类', kcal: 125, p: 20.2, c: 2.0, f: 3.6, fiber: 0, sugar: 0, sodium: 58, gi: 0, chol: 72, desc: '铁与锌含量较高的瘦牛肉部位', tags: ['补铁', '高蛋白'] },
      { id: 4, name: '鸡蛋', cat: '蛋类', kcal: 143, p: 12.6, c: 0.7, f: 9.5, fiber: 0, sugar: 0.4, sodium: 131, gi: 0, chol: 372, desc: '完整氨基酸组成，早餐常见蛋白来源', tags: ['全价蛋白'] },
      { id: 5, name: '北豆腐', cat: '豆制品', kcal: 116, p: 12.2, c: 3.0, f: 6.9, fiber: 0.4, sugar: 0.5, sodium: 7, gi: 15, desc: '植物蛋白，钙镁含量较好', tags: ['植物蛋白', '低钠'] },
      { id: 6, name: '鹰嘴豆', cat: '豆制品', kcal: 164, p: 8.9, c: 27.4, f: 2.6, fiber: 7.6, sugar: 4.8, sodium: 7, gi: 28, desc: '低 GI 主食型豆类，饱腹感强', tags: ['低GI', '高纤维'] },
      { id: 7, name: '燕麦', cat: '主食', kcal: 389, p: 16.9, c: 66.3, f: 6.9, fiber: 10.6, sugar: 0.8, sodium: 2, gi: 55, desc: 'β-葡聚糖有助延缓餐后血糖上升', tags: ['低GI', '高纤维'] },
      { id: 8, name: '藜麦', cat: '主食', kcal: 368, p: 14.1, c: 64.2, f: 6.1, fiber: 7.0, sugar: 6.0, sodium: 5, gi: 53, desc: '含全部必需氨基酸的伪谷物', tags: ['低GI', '高蛋白'] },
      { id: 9, name: '糙米饭', cat: '主食', kcal: 112, p: 2.6, c: 23.5, f: 0.8, fiber: 1.8, sugar: 0.4, sodium: 3, gi: 68, desc: '保留麸皮与胚芽，纤维高于白米', tags: ['粗粮'] },
      { id: 10, name: '白米饭', cat: '主食', kcal: 116, p: 2.6, c: 25.9, f: 0.3, fiber: 0.3, sugar: 0.1, sodium: 2, gi: 83, desc: '常见精制主食，GI 偏高需控量', tags: ['高GI'] },
      { id: 11, name: '红薯', cat: '主食', kcal: 86, p: 1.6, c: 20.1, f: 0.1, fiber: 3.0, sugar: 4.2, sodium: 28, gi: 77, desc: '富含 β-胡萝卜素与膳食纤维', tags: ['高纤维'] },
      { id: 12, name: '西兰花', cat: '蔬菜', kcal: 34, p: 2.8, c: 6.6, f: 0.4, fiber: 1.6, sugar: 1.5, sodium: 33, gi: 15, desc: '维生素 C 与硫苷类物质丰富', tags: ['高纤维', '低热量'] },
      { id: 13, name: '菠菜', cat: '蔬菜', kcal: 23, p: 2.9, c: 3.6, f: 0.4, fiber: 2.2, sugar: 0.4, sodium: 79, gi: 15, desc: '叶酸、铁、镁含量较高', tags: ['深色蔬菜'] },
      { id: 14, name: '番茄', cat: '蔬菜', kcal: 18, p: 0.9, c: 3.9, f: 0.2, fiber: 1.2, sugar: 2.6, sodium: 5, gi: 30, desc: '番茄红素与维生素 C 来源', tags: ['低热量'] },
      { id: 15, name: '黄瓜', cat: '蔬菜', kcal: 15, p: 0.8, c: 2.9, f: 0.2, fiber: 0.5, sugar: 1.7, sodium: 5, gi: 15, desc: '含水量高，适合做加餐或凉菜', tags: ['低热量'] },
      { id: 16, name: '牛油果', cat: '水果', kcal: 160, p: 2.0, c: 8.5, f: 14.7, fiber: 6.7, sugar: 0.7, sodium: 7, gi: 15, desc: '单不饱和脂肪酸丰富，热量密度高', tags: ['优质脂肪'] },
      { id: 17, name: '蓝莓', cat: '水果', kcal: 57, p: 0.7, c: 14.5, f: 0.3, fiber: 2.4, sugar: 10.0, sodium: 1, gi: 53, desc: '花青素含量高的低负担水果', tags: ['抗氧化'] },
      { id: 18, name: '苹果', cat: '水果', kcal: 52, p: 0.3, c: 13.5, f: 0.2, fiber: 1.7, sugar: 10.4, sodium: 1, gi: 36, desc: '果胶丰富，适合作为加餐', tags: ['低GI'] },
      { id: 19, name: '无糖希腊酸奶', cat: '乳制品', kcal: 59, p: 10.2, c: 3.6, f: 0.4, fiber: 0, sugar: 3.2, sodium: 36, gi: 35, desc: '浓缩发酵乳，蛋白密度高', tags: ['高蛋白', '益生菌'] },
      { id: 20, name: '低脂牛奶', cat: '乳制品', kcal: 54, p: 3.0, c: 3.4, f: 3.2, fiber: 0, sugar: 3.4, sodium: 44, gi: 30, desc: '钙与维生素 B2 的日常来源', tags: ['补钙'] },
      { id: 21, name: '杏仁', cat: '坚果', kcal: 579, p: 21.2, c: 21.6, f: 49.9, fiber: 12.5, sugar: 4.4, sodium: 1, gi: 15, desc: '维生素 E 与镁丰富，注意份量', tags: ['优质脂肪'] },
      { id: 22, name: '核桃', cat: '坚果', kcal: 654, p: 15.2, c: 13.7, f: 65.2, fiber: 6.7, sugar: 2.6, sodium: 2, gi: 15, desc: 'α-亚麻酸来源，每日一小把', tags: ['优质脂肪'] }
    ],

    /* ---------------- 食谱库 ---------------- */
    recipes: [
      {
        id: 1, name: '香煎鸡胸藜麦碗', desc: '高蛋白低脂的一碗式午餐，藜麦替代白米，饱腹又稳血糖。',
        mealType: '午餐', cuisine: '轻食', time: 25, level: '简单', servings: 1,
        kcal: 520, p: 42, c: 48, f: 16, fiber: 9,
        fit: ['减脂', '增肌'], rating: 4.8, views: 12840, collects: 862,
        img: ASSET + 'recipe-chicken.jpg',
        ingredients: [
          { name: '鸡胸肉', amount: '150', unit: 'g' },
          { name: '藜麦（生）', amount: '60', unit: 'g' },
          { name: '西兰花', amount: '150', unit: 'g' },
          { name: '小番茄', amount: '80', unit: 'g' },
          { name: '牛油果', amount: '40', unit: 'g' },
          { name: '橄榄油', amount: '5', unit: 'ml' }
        ],
        steps: [
          '藜麦冲洗后加 1.5 倍清水，中火煮 15 分钟至颗粒开花，关火焖 5 分钟。',
          '鸡胸肉横切成两片，用黑胡椒、少许盐和柠檬汁腌 10 分钟。',
          '平底锅刷薄油，中火煎鸡胸每面 3 分钟，静置 3 分钟后切片。',
          '西兰花焯水 90 秒，小番茄对半切，牛油果切片。',
          '所有食材码入碗中，淋上柠檬汁与少许橄榄油即可。'
        ],
        tips: '鸡胸煎好后静置再切，肉汁不会流失；藜麦一次可多煮两份冷藏。'
      },
      {
        id: 2, name: '三文鱼牛油果沙拉', desc: '优质脂肪与蛋白的组合，适合控糖期的晚餐或轻午餐。',
        mealType: '晚餐', cuisine: '西式', time: 18, level: '简单', servings: 1,
        kcal: 480, p: 32, c: 18, f: 30, fiber: 8,
        fit: ['控糖', '维持'], rating: 4.7, views: 9630, collects: 604,
        img: ASSET + 'recipe-salmon.jpg',
        ingredients: [
          { name: '三文鱼', amount: '150', unit: 'g' },
          { name: '芝麻菜 / 混合生菜', amount: '120', unit: 'g' },
          { name: '牛油果', amount: '60', unit: 'g' },
          { name: '黄瓜', amount: '80', unit: 'g' },
          { name: '南瓜籽', amount: '10', unit: 'g' },
          { name: '柠檬汁', amount: '10', unit: 'ml' }
        ],
        steps: [
          '三文鱼擦干水分，两面撒盐与黑胡椒。',
          '不粘锅中火带皮面朝下煎 3 分钟，翻面再煎 2 分钟。',
          '生菜洗净沥干，黄瓜切片，牛油果切块。',
          '柠檬汁 + 少许橄榄油 + 黑胡椒调成简易油醋汁。',
          '食材装盘，撒南瓜籽，淋汁即可。'
        ],
        tips: '三文鱼不必煎全熟，中心微粉口感更好；控糖期不额外加蜂蜜。'
      },
      {
        id: 3, name: '蓝莓燕麦早餐碗', desc: '10 分钟搞定的低 GI 早餐，β-葡聚糖帮助延缓血糖上升。',
        mealType: '早餐', cuisine: '西式', time: 10, level: '简单', servings: 1,
        kcal: 360, p: 14, c: 52, f: 9, fiber: 11,
        fit: ['减脂', '维持'], rating: 4.9, views: 15620, collects: 1120,
        img: ASSET + 'recipe-oatmeal.jpg',
        ingredients: [
          { name: '燕麦片', amount: '50', unit: 'g' },
          { name: '低脂牛奶', amount: '200', unit: 'ml' },
          { name: '蓝莓', amount: '80', unit: 'g' },
          { name: '香蕉', amount: '半根', unit: '' },
          { name: '核桃', amount: '10', unit: 'g' },
          { name: '奇亚籽', amount: '5', unit: 'g' }
        ],
        steps: [
          '燕麦片与牛奶倒入小锅，小火煮 4 分钟并不断搅拌。',
          '关火后加盖焖 2 分钟，让燕麦充分吸水。',
          '盛入碗中，铺上蓝莓、香蕉片与核桃碎。',
          '撒奇亚籽，可加少许肉桂粉提香。'
        ],
        tips: '乳糖不耐可换无糖豆奶；想增加蛋白可拌入 100g 希腊酸奶。'
      },
      {
        id: 4, name: '番茄牛腩蔬菜汤', desc: '一锅炖的暖胃晚餐，蛋白质与蔬菜纤维兼顾，少油少盐。',
        mealType: '晚餐', cuisine: '中式', time: 60, level: '中等', servings: 2,
        kcal: 410, p: 28, c: 24, f: 20, fiber: 6,
        fit: ['控糖', '维持'], rating: 4.6, views: 7860, collects: 431,
        img: ASSET + 'recipe-soup.jpg',
        ingredients: [
          { name: '牛腩', amount: '250', unit: 'g' },
          { name: '番茄', amount: '300', unit: 'g' },
          { name: '胡萝卜', amount: '150', unit: 'g' },
          { name: '西芹', amount: '100', unit: 'g' },
          { name: '洋葱', amount: '80', unit: 'g' },
          { name: '橄榄油', amount: '8', unit: 'ml' }
        ],
        steps: [
          '牛腩冷水下锅焯 3 分钟，撇去浮沫后捞出。',
          '锅中少油炒香洋葱，加入番茄炒出沙。',
          '放入牛腩与足量热水，小火炖 40 分钟。',
          '加入胡萝卜与西芹，再炖 12 分钟。',
          '出锅前用少许盐与黑胡椒调味，撒欧芹碎。'
        ],
        tips: '番茄先炒出沙再加水，汤色更浓；牛腩可换牛里脊降低脂肪。'
      },
      {
        id: 5, name: '时蔬鸡蛋全麦三明治', desc: '通勤早餐首选，蛋白 + 缓释碳水，10 分钟打包带走。',
        mealType: '早餐', cuisine: '西式', time: 12, level: '简单', servings: 1,
        kcal: 340, p: 18, c: 38, f: 12, fiber: 6,
        fit: ['减脂'], rating: 4.5, views: 6430, collects: 352,
        img: ASSET + 'article-vegetables.jpg',
        ingredients: [
          { name: '全麦吐司', amount: '2', unit: '片' },
          { name: '鸡蛋', amount: '1', unit: '个' },
          { name: '生菜', amount: '40', unit: 'g' },
          { name: '番茄', amount: '50', unit: 'g' },
          { name: '无糖酸奶', amount: '15', unit: 'g' }
        ],
        steps: [
          '鸡蛋煮熟切片，番茄切薄片，生菜洗净沥干。',
          '全麦吐司烤 2 分钟至微脆。',
          '用酸奶替代沙拉酱涂抹吐司，减少额外油脂。',
          '依次铺生菜、番茄、鸡蛋，合上吐司对半切。'
        ],
        tips: '用酸奶替代沙拉酱，一份可少约 80 kcal。'
      },
      {
        id: 6, name: '清蒸鲈鱼配糙米', desc: '中式少油做法，优质蛋白搭配粗粮，适合家庭晚餐。',
        mealType: '晚餐', cuisine: '中式', time: 30, level: '中等', servings: 2,
        kcal: 450, p: 35, c: 42, f: 12, fiber: 4,
        fit: ['减脂', '控糖'], rating: 4.7, views: 8920, collects: 523,
        img: ASSET + 'recipe-salmon.jpg',
        ingredients: [
          { name: '鲈鱼', amount: '400', unit: 'g' },
          { name: '糙米（生）', amount: '80', unit: 'g' },
          { name: '姜丝', amount: '10', unit: 'g' },
          { name: '小葱', amount: '20', unit: 'g' },
          { name: '蒸鱼豉油', amount: '10', unit: 'ml' }
        ],
        steps: [
          '糙米提前浸泡 30 分钟，按 1:1.4 水米比煮成饭。',
          '鲈鱼处理干净，两面划刀，铺姜丝。',
          '水开后上锅大火蒸 8 分钟，关火焖 2 分钟。',
          '倒掉盘中腥水，铺葱丝，淋蒸鱼豉油。',
          '浇一小勺热油激香，配糙米饭食用。'
        ],
        tips: '蒸鱼时间按每 500g 8 分钟控制，过久肉质会柴。'
      },
      {
        id: 7, name: '豆腐菌菇暖锅', desc: '植物蛋白为主的低负担晚餐，一锅补充膳食纤维。',
        mealType: '晚餐', cuisine: '中式', time: 25, level: '简单', servings: 2,
        kcal: 320, p: 22, c: 26, f: 13, fiber: 8,
        fit: ['减脂', '维持'], rating: 4.4, views: 5120, collects: 268,
        img: ASSET + 'recipe-soup.jpg',
        ingredients: [
          { name: '北豆腐', amount: '300', unit: 'g' },
          { name: '香菇', amount: '100', unit: 'g' },
          { name: '金针菇', amount: '100', unit: 'g' },
          { name: '娃娃菜', amount: '200', unit: 'g' },
          { name: '味噌', amount: '15', unit: 'g' }
        ],
        steps: [
          '豆腐切厚片，香菇划十字，娃娃菜切段。',
          '锅中加 600ml 清水，放入香菇煮 8 分钟出味。',
          '加入豆腐与娃娃菜，小火煮 6 分钟。',
          '味噌用少量温水化开后倒入，加入金针菇煮 2 分钟。'
        ],
        tips: '味噌最后放，避免久煮损失风味；需要更多蛋白可加虾仁。'
      },
      {
        id: 8, name: '希腊酸奶坚果杯', desc: '下午加餐的稳定选择，蛋白 + 好脂肪，避免精制糖。',
        mealType: '加餐', cuisine: '西式', time: 5, level: '简单', servings: 1,
        kcal: 210, p: 12, c: 18, f: 10, fiber: 4,
        fit: ['减脂', '增肌'], rating: 4.6, views: 4380, collects: 214,
        img: ASSET + 'recipe-oatmeal.jpg',
        ingredients: [
          { name: '无糖希腊酸奶', amount: '150', unit: 'g' },
          { name: '蓝莓', amount: '50', unit: 'g' },
          { name: '杏仁', amount: '8', unit: 'g' },
          { name: '奇亚籽', amount: '5', unit: 'g' }
        ],
        steps: [
          '酸奶倒入杯中。',
          '铺上蓝莓，撒杏仁碎与奇亚籽。',
          '冷藏 5 分钟口感更佳。'
        ],
        tips: '选择配料表只有生牛乳与菌种的酸奶，避免风味发酵乳。'
      },
      {
        id: 9, name: '彩椒牛肉藜麦饭', desc: '增肌期的高蛋白主食碗，铁与维生素 C 同时补足。',
        mealType: '午餐', cuisine: '中式', time: 30, level: '中等', servings: 1,
        kcal: 560, p: 38, c: 55, f: 18, fiber: 7,
        fit: ['增肌', '维持'], rating: 4.7, views: 7340, collects: 396,
        img: ASSET + 'recipe-chicken.jpg',
        ingredients: [
          { name: '牛里脊', amount: '120', unit: 'g' },
          { name: '藜麦（生）', amount: '70', unit: 'g' },
          { name: '彩椒', amount: '100', unit: 'g' },
          { name: '洋葱', amount: '50', unit: 'g' },
          { name: '生抽', amount: '8', unit: 'ml' }
        ],
        steps: [
          '藜麦煮熟备用，牛里脊逆纹切片。',
          '牛肉用生抽与黑胡椒抓匀，腌 8 分钟。',
          '热锅快炒牛肉至变色盛出。',
          '炒香洋葱与彩椒，回锅牛肉，调入少许黑胡椒。',
          '铺在藜麦饭上即可。'
        ],
        tips: '牛肉逆纹切、全程大火快炒，口感更嫩。'
      }
    ],

    /* ---------------- 健康文章 ---------------- */
    articles: [
      {
        id: 1, title: '减脂期也要吃碳水：三种低 GI 主食怎么选',
        summary: '完全戒碳水会让训练表现和情绪一起下滑。把白米换成低 GI 主食，是更容易长期坚持的做法。',
        cat: '减肥指南', tags: ['低GI', '主食', '减脂'], author: '注册营养师 · 周昀',
        date: '2026-10-18', views: 8620, likes: 412, collects: 286, comments: 3,
        cover: ASSET + 'article-vegetables.jpg',
        body: [
          { t: 'p', text: '减脂最常见的误区之一，是把碳水化合物当成敌人。事实上，碳水是大脑和肌肉的主要燃料，长期摄入过低往往带来注意力下降、训练无力与报复性进食。' },
          { t: 'h2', text: '先理解 GI：不是越低越好' },
          { t: 'p', text: 'GI（血糖生成指数）描述的是食物升高血糖的速度。低 GI 食物消化吸收更慢，餐后血糖曲线更平缓，饱腹感也更持久。但 GI 只反映速度，不反映总量——低 GI 食物吃多了，热量一样会超标。' },
          { t: 'quote', text: '选择低 GI 主食的价值在于「更容易控制总量」，而不是获得了可以无限吃的许可。' },
          { t: 'h2', text: '三种值得常备的主食' },
          { t: 'ul', items: ['藜麦：蛋白质约 14%，含全部必需氨基酸，GI 约 53，适合替代部分白米。', '燕麦：β-葡聚糖有助延缓胃排空，选择原味燕麦片而非即食甜味麦片。', '糙米 / 杂粮饭：保留麸皮与胚芽，纤维明显高于白米，建议先按 1:1 与白米混合。'] },
          { t: 'p', text: '实操上不必一步到位。把一顿饭里的白米换成杂粮饭，或把早餐的甜面包换成燕麦碗，通常就能让全天膳食纤维提高 5–8g。' },
          { t: 'h2', text: '份量比种类更关键' },
          { t: 'p', text: '成年女性减脂期每餐主食（熟重）建议控制在 100–150g，男性可到 150–200g，再根据活动量和饥饿感微调。搭配足量蛋白质与蔬菜，血糖曲线会更平稳。' },
          { t: 'p', text: '需要提醒的是，本文提供的是通用营养建议，不构成医疗诊断。若你正在使用降糖药物或存在糖尿病、肾病等情况，请先咨询医生或临床营养师。' }
        ]
      },
      {
        id: 2, title: '高血脂人群的饮食清单：先改这 6 个习惯',
        summary: '不必立刻吃得「寡淡」。从烹调油、主食结构到鱼类摄入，六个可执行的调整比一份忌口清单更有用。',
        cat: '饮食指南', tags: ['高血脂', '慢病', '食养指南'], author: '平台编辑部',
        date: '2026-10-15', views: 12460, likes: 731, collects: 512, comments: 5,
        cover: ASSET + 'recipe-salmon.jpg',
        body: [
          { t: 'p', text: '血脂异常的管理首先是生活方式管理。饮食调整的重点通常不是「完全不吃油」，而是调整脂肪的种类与总量。' },
          { t: 'h2', text: '六个优先动作' },
          { t: 'ul', items: ['把部分饱和脂肪（肥肉、黄油、椰子油）换成不饱和脂肪（橄榄油、菜籽油、坚果）。', '每周吃 2 次深海鱼，补充 Omega-3。', '主食一半换成全谷物或杂豆，增加可溶性膳食纤维。', '每天蔬菜 300–500g，深色蔬菜占一半。', '限制含糖饮料与精制甜点，控制添加糖。', '减少加工肉制品，优先选择瘦肉、禽肉和豆制品。'] },
          { t: 'quote', text: '以上内容参考《中国居民膳食指南》与成人血脂异常食养指南的通用原则，具体方案请遵医嘱。' },
          { t: 'p', text: '如果正在服用降脂药物，不要自行停药或仅靠饮食替代治疗。饮食与运动是基础，但不能替代医生的处方。' }
        ]
      },
      {
        id: 3, title: '蛋白质到底吃多少？用体重算出你的每日下限',
        summary: '1.2g/kg 还是 2.0g/kg？先看目标，再看训练量，最后才谈补剂。',
        cat: '营养知识', tags: ['蛋白质', '增肌', '基础'], author: '注册营养师 · 周昀',
        date: '2026-10-12', views: 6890, likes: 328, collects: 241, comments: 2,
        cover: ASSET + 'recipe-chicken.jpg',
        body: [
          { t: 'p', text: '蛋白质的推荐量应按体重计算，而不是按「每餐一个鸡蛋」估算。普通久坐人群约 1.0–1.2g/kg，规律力量训练者可到 1.6–2.0g/kg。' },
          { t: 'h2', text: '把总量拆到三餐' },
          { t: 'p', text: '一次摄入 20–30g 蛋白质更利于肌肉合成。以 60kg、目标 1.5g/kg 为例，全天约 90g，可拆成早餐 20g、午餐 30g、晚餐 30g、加餐 10g。' },
          { t: 'ul', items: ['100g 鸡胸肉 ≈ 31g 蛋白质', '1 个鸡蛋 ≈ 6g 蛋白质', '150g 希腊酸奶 ≈ 15g 蛋白质', '100g 北豆腐 ≈ 12g 蛋白质'] },
          { t: 'p', text: '肾功能异常人群不应自行提高蛋白摄入，需由医生或临床营养师评估。' }
        ]
      },
      {
        id: 4, title: '外卖党的一日三餐：这样点不超标',
        summary: '同样是小炒肉，盖饭和单点菜的差距可能超过 300 kcal。四个点单顺序帮你少踩坑。',
        cat: '饮食指南', tags: ['外卖', '实操', '热量'], author: '平台编辑部',
        date: '2026-10-09', views: 5430, likes: 296, collects: 187, comments: 1,
        cover: ASSET + 'recipe-soup.jpg',
        body: [
          { t: 'p', text: '外卖不是健康的反面，关键在于结构：先保证蛋白质和蔬菜，再控制主食与酱汁。' },
          { t: 'ul', items: ['优先单点菜 + 小份米饭，避免盖浇饭（酱汁会全部渗进米饭）。', '点一份清蒸、白灼或烤制的蛋白质，避开糖醋、红烧、干锅。', '主动加一份蔬菜，或自带小番茄、黄瓜。', '酱汁分装，蘸着吃而不是拌着吃。'] }
        ]
      },
      {
        id: 5, title: '隐形糖地图：那些「不甜」的高糖食物',
        summary: '番茄酱、沙拉酱、风味酸奶、即食麦片——甜味不明显，添加糖却不少。',
        cat: '饮食误区', tags: ['添加糖', '标签', '误区'], author: '平台编辑部',
        date: '2026-10-06', views: 4780, likes: 241, collects: 152, comments: 2,
        cover: ASSET + 'article-vegetables.jpg',
        body: [
          { t: 'p', text: '看配料表时，糖常以多种名字出现：白砂糖、果葡糖浆、麦芽糊精、浓缩果汁、蜂蜜。配料表按含量降序排列，糖排得越前，含量越高。' },
          { t: 'ul', items: ['风味酸奶：一份 150g 可能含 12–18g 糖。', '沙拉酱：一勺约 4g 糖与 10g 脂肪。', '番茄酱：每 100g 添加糖可达 20g 以上。', '即食麦片：常与糖、果干、糖浆同时出现。'] }
        ]
      },
      {
        id: 6, title: '增肌期怎么吃：热量盈余与训练日加餐',
        summary: '增肌不是无限吃。先设定 10%–15% 的温和盈余，再把加餐放在训练前后。',
        cat: '增肌指南', tags: ['增肌', '热量盈余', '加餐'], author: '体能教练 · 陈牧',
        date: '2026-10-03', views: 6210, likes: 352, collects: 226, comments: 2,
        cover: ASSET + 'recipe-chicken.jpg',
        body: [
          { t: 'p', text: '增肌的核心是渐进超负荷训练 + 温和热量盈余 + 足够蛋白。热量盈余过大，增加的主要是脂肪。' },
          { t: 'ul', items: ['先算维持热量，再加 10%–15%。', '蛋白质 1.6–2.0g/kg，分散到 4 餐。', '训练后 1–2 小时内补充 30–40g 蛋白与 40–60g 碳水。', '每周体重增长控制在 0.25%–0.5% 体重。'] }
        ]
      },
      {
        id: 7, title: '膳食纤维：肠道与血糖的双重护城河',
        summary: '每天 25–30g 纤维并不难，难的是吃对种类。可溶性纤维与不可溶性纤维要搭配。',
        cat: '营养知识', tags: ['膳食纤维', '肠道', '血糖'], author: '注册营养师 · 周昀',
        date: '2026-09-28', views: 3980, likes: 186, collects: 134, comments: 0,
        cover: ASSET + 'article-vegetables.jpg',
        body: [
          { t: 'p', text: '可溶性纤维（燕麦 β-葡聚糖、果胶、豆类）有助延缓糖吸收；不可溶性纤维（麸皮、蔬菜茎叶）促进肠道蠕动。' },
          { t: 'ul', items: ['早餐：50g 燕麦 ≈ 5g 纤维', '午餐：150g 西兰花 ≈ 2.4g', '加餐：1 个苹果 ≈ 1.7g', '晚餐：100g 鹰嘴豆 ≈ 7.6g'] }
        ]
      },
      {
        id: 8, title: '痛风人群的饮食误区：豆制品真的不能吃吗',
        summary: '植物嘌呤与动物嘌呤的风险并不相同。与其一刀切，不如先控酒精与果糖。',
        cat: '饮食误区', tags: ['痛风', '豆制品', '慢病'], author: '平台编辑部',
        date: '2026-09-24', views: 5120, likes: 264, collects: 168, comments: 1,
        cover: ASSET + 'recipe-soup.jpg',
        body: [
          { t: 'p', text: '多项研究提示，适量豆制品与痛风发作风险升高并无明确关联，真正需要优先限制的是酒精（尤其啤酒）、含糖饮料与高嘌呤内脏、浓肉汤。' },
          { t: 'p', text: '急性发作期仍应遵医嘱调整饮食。本文仅为通用科普，不替代医疗建议。' }
        ]
      }
    ],

    /* ---------------- 今日饮食记录 ---------------- */
    records: [
      {
        id: 'r-1001', date: '2026-10-23', mealType: '早餐', time: '08:10', note: '晨跑后',
        items: [
          { name: '燕麦片', amount: 50, unit: 'g', kcal: 195, p: 8.5, c: 33.2, f: 3.5 },
          { name: '低脂牛奶', amount: 200, unit: 'ml', kcal: 108, p: 6.0, c: 6.8, f: 6.4 },
          { name: '蓝莓', amount: 80, unit: 'g', kcal: 46, p: 0.6, c: 11.6, f: 0.2 }
        ]
      },
      {
        id: 'r-1002', date: '2026-10-23', mealType: '午餐', time: '12:35', note: '公司食堂',
        items: [
          { name: '白米饭', amount: 150, unit: 'g', kcal: 174, p: 3.9, c: 38.9, f: 0.5 },
          { name: '鸡胸肉', amount: 120, unit: 'g', kcal: 198, p: 37.2, c: 0, f: 4.3 },
          { name: '西兰花', amount: 150, unit: 'g', kcal: 51, p: 4.2, c: 9.9, f: 0.6 }
        ]
      }
    ],

    /* 近 7 日摄入（用于趋势图；真实实现由 /record/analysis/trend 返回） */
    trend7: [
      { date: '10-17', kcal: 1760, p: 92, c: 208, f: 56 },
      { date: '10-18', kcal: 1920, p: 104, c: 226, f: 62 },
      { date: '10-19', kcal: 1680, p: 96, c: 186, f: 52 },
      { date: '10-20', kcal: 1830, p: 108, c: 198, f: 58 },
      { date: '10-21', kcal: 1740, p: 101, c: 192, f: 55 },
      { date: '10-22', kcal: 1880, p: 112, c: 205, f: 60 },
      { date: '10-23', kcal: 772, p: 60.4, c: 100.4, f: 15.5 }
    ],

    /* ---------------- 通知 ---------------- */
    notifications: [
      { id: 1, type: '目标达成', title: '本周目标完成度 86%', content: '你已连续 5 天热量摄入在目标区间内，继续保持。', time: '2026-10-23 08:02', read: false, link: 'goal.html' },
      { id: 2, type: '饮食提醒', title: '午餐还没记录哦', content: '今天午餐摄入约 423 kcal，记录后可获得更准确的建议。', time: '2026-10-23 13:10', read: false, link: 'record.html' },
      { id: 3, type: '文章推荐', title: '为你推荐：高血脂人群的饮食清单', content: '根据你的健康档案与收藏偏好，这篇文章可能对你有帮助。', time: '2026-10-22 20:15', read: false, link: 'article-detail.html?id=2' },
      { id: 4, type: '系统', title: 'AI 助手已支持流式回复', content: '回答将逐字输出，并标注意图与知识来源，方便你判断可信度。', time: '2026-10-21 10:30', read: true, link: 'assistant.html' },
      { id: 5, type: '目标达成', title: '体重下降 0.4kg', content: '距目标体重还差 6.4kg，当前进度 47%。', time: '2026-10-20 07:45', read: true, link: 'health.html' },
      { id: 6, type: '警告', title: '今日蛋白质摄入偏低', content: '截至 21:00 蛋白质摄入 61g，低于目标 135g，可补充一份希腊酸奶。', time: '2026-10-19 21:05', read: true, link: 'record.html' }
    ],

    /* ---------------- AI 会话 ---------------- */
    conversations: [
      {
        id: 'c1', title: '高血脂饮食要注意什么', summary: '检索了权威食养指南，给出 6 条可执行建议', time: '10-23 09:12',
        messages: [
          { role: 'user', text: '高血脂人群饮食要注意什么？' },
          {
            role: 'ai', intent: 'knowledge', source: 'authority', text: '结合权威食养指南，高血脂人群的饮食调整可以优先做这几件事：',
            list: ['减少饱和脂肪：肥肉、黄油、椰子油、奶油点心尽量少吃，烹调油换成橄榄油或菜籽油。', '增加不饱和脂肪：每周吃 2 次深海鱼，每天一小把原味坚果（约 10g）。', '主食一半换全谷物或杂豆，增加可溶性膳食纤维。', '每天蔬菜 300–500g，深色蔬菜占一半。', '限制含糖饮料与精制甜点，控制添加糖在 25g 以内。', '减少加工肉制品，优先瘦肉、禽肉与豆制品。'],
            note: '以上为通用营养建议，具体方案请遵医嘱。'
          }
        ]
      },
      {
        id: 'c2', title: '鸡胸肉可以用什么替代', summary: '按蛋白与脂肪做了等价替换，返回 3 个食材卡片', time: '10-22 18:40',
        messages: [
          { role: 'user', text: '鸡胸肉可以用什么低脂食材替代？' },
          {
            role: 'ai', intent: 'advice', source: 'ingredient', text: '按「每 100g 蛋白质 ≥ 12g、脂肪 ≤ 7g」筛选，以下三种替换比较接近：',
            cards: [
              { title: '北豆腐', sub: '116 kcal · 蛋白 12.2g · 脂肪 6.9g', img: ASSET + 'article-vegetables.jpg', href: 'ingredients.html' },
              { title: '鹰嘴豆', sub: '164 kcal · 蛋白 8.9g · 纤维 7.6g', img: ASSET + 'recipe-soup.jpg', href: 'ingredients.html' },
              { title: '牛里脊', sub: '125 kcal · 蛋白 20.2g · 脂肪 3.6g', img: ASSET + 'recipe-chicken.jpg', href: 'ingredients.html' }
            ],
            note: '替换时注意同步调整用量，保持这一餐的蛋白质总量不变。'
          }
        ]
      },
      {
        id: 'c3', title: '减脂期一周早餐怎么搭', summary: '给出了 5 套早餐组合与热量区间', time: '10-20 08:05',
        messages: [
          { role: 'user', text: '我在减脂，一周早餐怎么搭配比较不容易饿？' },
          {
            role: 'ai', intent: 'advice', source: 'article', text: '你的目标是 1800 kcal，早餐建议控制在 350–420 kcal，并保证 20g 以上蛋白质。可以这样轮换：',
            list: ['燕麦碗：燕麦 50g + 牛奶 200ml + 蓝莓 80g + 核桃 10g（约 360 kcal / 14g 蛋白）', '全麦三明治：全麦吐司 2 片 + 鸡蛋 1 个 + 生菜番茄（约 340 kcal / 18g 蛋白）', '希腊酸奶杯：酸奶 150g + 蓝莓 50g + 杏仁 8g + 奇亚籽 5g（约 210 kcal，可加半根香蕉）', '杂粮粥 + 水煮蛋 + 凉拌菠菜（约 380 kcal / 21g 蛋白）', '藜麦鸡蛋沙拉（约 400 kcal / 22g 蛋白）'],
            note: '蛋白质前置能明显降低上午的饥饿感。'
          }
        ]
      }
    ],

    /* ---------------- 后台总览 ---------------- */
    admin: {
      overview: {
        users: 1284, ingredients: 236, recipes: 148, articles: 96, notifications: 42,
        dau: 386, records: 5217
      },
      trend7: [
        { date: '10-17', users: 312, records: 684 },
        { date: '10-18', users: 348, records: 742 },
        { date: '10-19', users: 326, records: 701 },
        { date: '10-20', users: 371, records: 815 },
        { date: '10-21', users: 402, records: 863 },
        { date: '10-22', users: 395, records: 842 },
        { date: '10-23', users: 386, records: 5217 }
      ],
      activities: [
        { text: '管理员 周昀 发布了食谱《清蒸鲈鱼配糙米》', time: '10 分钟前', type: 'green' },
        { text: '用户 138****2043 提交了午餐记录（3 项明细）', time: '18 分钟前', type: 'green' },
        { text: 'AI 助手命中医疗越界拦截 1 次，已记录审计日志', time: '32 分钟前', type: 'amber' },
        { text: '知识库 authority 源重建完成，切块 4,218 条', time: '1 小时前', type: 'green' },
        { text: '文章《外卖党的一日三餐》进入热门榜第 4 位', time: '2 小时前', type: 'gray' },
        { text: '用户 139****7710 被禁用（多次违规评论）', time: '3 小时前', type: 'amber' }
      ],
      users: [
        { id: 1024, name: '林嘉禾', email: 'jiahe@example.com', goal: '减脂', records: 128, status: 1, joined: '2026-08-12' },
        { id: 1025, name: '陈嘉宁', email: 'jianing@example.com', goal: '增肌', records: 96, status: 1, joined: '2026-08-19' },
        { id: 1026, name: '周予安', email: 'yuan@example.com', goal: '控糖', records: 74, status: 1, joined: '2026-08-25' },
        { id: 1027, name: '许知遥', email: 'zhiyao@example.com', goal: '维持', records: 41, status: 1, joined: '2026-09-02' },
        { id: 1028, name: '赵思齐', email: 'siqi@example.com', goal: '减脂', records: 152, status: 1, joined: '2026-09-08' },
        { id: 1029, name: '钱一诺', email: 'yinuo@example.com', goal: '增肌', records: 63, status: 0, joined: '2026-09-11' },
        { id: 1030, name: '孙可岚', email: 'kelan@example.com', goal: '控糖', records: 87, status: 1, joined: '2026-09-17' },
        { id: 1031, name: '李维清', email: 'weiqing@example.com', goal: '维持', records: 22, status: 1, joined: '2026-09-23' },
        { id: 1032, name: '吴听澜', email: 'tinglan@example.com', goal: '减脂', records: 109, status: 1, joined: '2026-09-29' },
        { id: 1033, name: '郑栖迟', email: 'qichi@example.com', goal: '增肌', records: 35, status: 1, joined: '2026-10-04' }
      ]
    }
  };

  window.DB = DB;
})();
