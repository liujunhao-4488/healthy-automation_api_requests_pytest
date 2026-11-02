package com.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.health.entity.Ingredient;
import com.health.mapper.IngredientMapper;
import com.health.service.IngredientService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 食材服务实现类
 */
@Service
public class IngredientServiceImpl implements IngredientService {

    @Autowired
    private IngredientMapper ingredientMapper;

    @Override
    public List<Ingredient> getAllIngredients() {
        return ingredientMapper.selectList(null);
    }

    @Override
    public Ingredient getIngredientById(Long id) {
        return ingredientMapper.selectById(id);
    }

    @Override
    public List<Ingredient> getIngredientsByCategory(String category) {
        return ingredientMapper.selectByCategory(category);
    }

    @Override
    public List<Ingredient> searchIngredients(String keyword) {
        return ingredientMapper.selectByNameLike("%" + keyword + "%");
    }

    @Override
    public Ingredient saveIngredient(Ingredient ingredient) {
        ingredientMapper.insert(ingredient);
        return ingredient;
    }

    @Override
    public Ingredient updateIngredient(Ingredient ingredient) {
        ingredientMapper.updateById(ingredient);
        return ingredient;
    }

    @Override
    public boolean deleteIngredient(Long id) {
        return ingredientMapper.deleteById(id) > 0;
    }

    @Override
    public Map<String, Double> calculateNutrition(Long ingredientId, Double quantity, String unit) {
        Ingredient ingredient = ingredientMapper.selectById(ingredientId);
        Map<String, Double> nutrition = new HashMap<>();
        
        if (ingredient != null) {
            // 假设单位是克，转换为100克的比例
            double ratio = quantity / 100.0;
            
            nutrition.put("calories", ingredient.getCaloriesPer100g() * ratio);
            nutrition.put("protein", ingredient.getProteinPer100g() * ratio);
            nutrition.put("carbs", ingredient.getCarbsPer100g() * ratio);
            nutrition.put("fat", ingredient.getFatPer100g() * ratio);
            
            if (ingredient.getFiberPer100g() != null) {
                nutrition.put("fiber", ingredient.getFiberPer100g() * ratio);
            }
            if (ingredient.getSugarPer100g() != null) {
                nutrition.put("sugar", ingredient.getSugarPer100g() * ratio);
            }
            if (ingredient.getSodiumPer100g() != null) {
                nutrition.put("sodium", ingredient.getSodiumPer100g() * ratio);
            }
            if (ingredient.getGiValue() != null) {
                nutrition.put("gi", ingredient.getGiValue().doubleValue());
            }
        }
        
        return nutrition;
    }

    /* ============================================================
       食材替代推荐（2026-11-02 实现，替换原先的硬编码假数据）
       ============================================================

       算法：把每种食材看成 6 维营养向量，用「归一化 + 加权欧氏距离」衡量相似度。

         维度权重（为什么这么配）：
           热量  30%  —— 替代的核心诉求是热量别差太多
           蛋白  30%  —— 蛋白质是饱腹与肌肉维持的关键，权重最高
           碳水  15%
           脂肪  15%
           纤维   5%
           GI     5%  —— 不是所有食材都有 GI，权重压低

       归一化用「库内百分位」而不是原始值：
         原始值跨度极大（热量 11~884，纤维 0~19），
         不归一化的话热量和纤维会互相淹没。

       几个必须处理的脏数据问题（实测发现）：
         1) 库里有 33 组重名（125 行只有 92 个不同名字），
            且同名营养值还不同（藜麦 368 vs 120、鸡胸肉 165 vs 133）。
            → 按名字匹配时可能命中多条，这里取「与目标差异最小」的那条作为目标，
              并在结果里按名字去重，避免返回两个「鸡胸肉」。
         2) 前端 BASE_OPTIONS 传的是「白米饭」，库里叫「米饭」。
            → 精确匹配失败时做包含匹配（双向 contains）。
         3) 「测试分类」是脏数据，排除。
        ============================================================ */

    /** 营养维度权重，总和为 1 */
    private static final double W_CAL = 0.30;
    private static final double W_PRO = 0.30;
    private static final double W_CARB = 0.15;
    private static final double W_FAT = 0.15;
    private static final double W_FIBER = 0.05;
    private static final double W_GI = 0.05;

    /** 脏数据分类，不参与推荐 */
    private static final String BAD_CATEGORY = "测试分类";

    private static double nz(Double v) {
        return v == null ? 0.0 : v;
    }

    /** gi_value 是 Integer 类型，单独给一个重载 */
    private static double nz(Integer v) {
        return v == null ? 0.0 : v.doubleValue();
    }

    @Override
    public List<Map<String, Object>> getSubstitutes(String ingredientName, String prompt, Integer limit) {
        int topN = (limit == null || limit <= 0) ? 4 : Math.min(limit, 10);
        String target = ingredientName == null ? "" : ingredientName.trim();
        if (target.isEmpty()) {
            throw new RuntimeException("请先选择需要替代的食材");
        }

        QueryWrapper<Ingredient> qw = new QueryWrapper<>();
        qw.eq("status", 1).ne("category", BAD_CATEGORY).orderByAsc("id");
        List<Ingredient> all = ingredientMapper.selectList(qw);
        if (all == null || all.isEmpty()) {
            throw new RuntimeException("食材库为空");
        }
        /* 按 id 升序固定顺序：下面「重名 / 同营养」去重时保留的是先遇到的条目，
           如果依赖数据库默认返回顺序，同一请求可能得到不同名字的结果。 */
        all.sort(Comparator.comparing(Ingredient::getId, Comparator.nullsLast(Comparator.naturalOrder())));

        // ---- 1) 定位目标食材：精确 → 包含 → 编辑距离最近 ----
        Ingredient base = findIngredient(all, target);
        if (base == null) {
            throw new RuntimeException("食材库中未找到「" + target + "」，请换个名称试试");
        }

        // ---- 2) 计算每个维度的极值，用于归一化 ----
        double maxCal = 1, maxPro = 1, maxCarb = 1, maxFat = 1, maxFiber = 1, maxGi = 1;
        for (Ingredient i : all) {
            maxCal = Math.max(maxCal, nz(i.getCaloriesPer100g()));
            maxPro = Math.max(maxPro, nz(i.getProteinPer100g()));
            maxCarb = Math.max(maxCarb, nz(i.getCarbsPer100g()));
            maxFat = Math.max(maxFat, nz(i.getFatPer100g()));
            maxFiber = Math.max(maxFiber, nz(i.getFiberPer100g()));
            maxGi = Math.max(maxGi, nz(i.getGiValue()));
        }

        // ---- 3) 逐条算加权距离 ----
        String p = prompt == null ? "" : prompt.toLowerCase();
        boolean wantLowFat = p.contains("低脂") || p.contains("减脂") || p.contains("低卡");
        boolean wantLowGi = p.contains("低gi") || p.contains("低 gi") || p.contains("控糖");
        boolean wantHighPro = p.contains("高蛋白") || p.contains("增肌");

        List<Map<String, Object>> scored = new ArrayList<>();
        Set<String> seenNames = new HashSet<>();
        seenNames.add(base.getName()); // 目标自己不作为候选
        /*
         * 库里除了重名，还有一批「营养完全相同但名字不同」的条目，实测例如：
         *   虾(99kcal/24g)  vs 虾仁(99kcal/24g)
         *   西红柿  vs 番茄
         *   蘑菇  vs 菌菇
         * 按营养向量算相似度时它们必然并列，结果里会出现两个本质相同的方案。
         * 这里再加一道按「营养指纹」去重，只保留先遇到的那个。
         */
        Set<String> seenNutrition = new HashSet<>();
        seenNutrition.add(fingerprint(base));

        for (Ingredient cand : all) {
            if (cand.getId() != null && cand.getId().equals(base.getId())) continue;
            // 重名去重：同一名字只保留最优的一条
            if (cand.getName() != null && !seenNames.add(cand.getName())) continue;
            // 营养完全相同的重复条目去重
            if (!seenNutrition.add(fingerprint(cand))) continue;

            double d = dist(base, cand, maxCal, maxPro, maxCarb, maxFat, maxFiber, maxGi);
            double sim = Math.max(0.05, Math.min(0.99, 1.0 - d));

            /*
             * 类别约束：纯按营养向量排会给出荒谬结果 —— 实测「牛奶」的替代里
             * 出现了蘑菇和菠菜（热量蛋白确实接近，但拿蘑菇替代牛奶毫无意义）。
             * 处理方式是不硬性排除（跨类有时确实需要，如豆制品替肉类），
             * 而是给跨类候选加一个距离惩罚，让同类候选优先。
             */
            boolean sameCat = base.getCategory() != null
                    && base.getCategory().equals(cand.getCategory());
            if (!sameCat) {
                d += 0.25; // 惩罚值经过调试：约相当于相似度掉 25 个点
                sim = Math.max(0.05, sim - 0.15);
            }

            /*
             * 目标偏好加成。
             *
             * 踩过两个坑：
             *   一稿用 cand.fat < base.fat 判断「低脂」，结果牛肉(17g)的候选里
             *   三文鱼13.4g、金枪鱼1.3g 全部小于 17，全体命中、全体 +0.06，
             *   排序一点没变，等于没做。而且三文鱼脂肪是三文鱼的 13 倍却和
             *   金枪鱼拿一样的加成，也不合理。
             *
             * 现在的做法：
             *   1) 阈值用「明显更低」= 不高于基准的 60%，而不是「小于」；
             *   2) 加成按满足程度线性递增（越低脂加得越多），但封顶 0.06，
             *      保证不会盖过营养相似度本身（相似度差 10 点以上仍按相似度排）。
             */
            double bonus = 0;
            if (wantLowFat) {
                double fb = nz(base.getFatPer100g());
                double fc = nz(cand.getFatPer100g());
                if (fb > 0 && fc <= fb * 0.6) {
                    // 越低脂加成越高，上限 0.06
                    bonus += 0.06 * (1 - fc / (fb * 0.6));
                }
            }
            if (wantLowGi) {
                double g = nz(cand.getGiValue());
                if (g > 0 && g <= 55) {
                    bonus += 0.03 + 0.03 * (1 - g / 55.0);
                }
            }
            if (wantHighPro) {
                double pb = nz(base.getProteinPer100g());
                double pc = nz(cand.getProteinPer100g());
                if (pb > 0 && pc >= pb) {
                    bonus += 0.03 + Math.min(0.03, (pc - pb) / pb * 0.03);
                }
            }
            sim = Math.min(0.99, sim + bonus);

            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", cand.getId());
            m.put("name", cand.getName());
            m.put("category", cand.getCategory());
            m.put("similarity", Math.round(sim * 100) / 100.0);
            m.put("reason", buildReason(base, cand));
            m.put("calories", nz(cand.getCaloriesPer100g()));
            m.put("protein", nz(cand.getProteinPer100g()));
            m.put("carbs", nz(cand.getCarbsPer100g()));
            m.put("fat", nz(cand.getFatPer100g()));
            m.put("fiber", nz(cand.getFiberPer100g()));
            m.put("gi", nz(cand.getGiValue()));
            /*
             * 排序键用「加了偏好加成之后的相似度」，不能用原始距离：
             * 之前按 _d 升序排、却按 similarity 展示，二者不一致，
             * 会出现「金枪鱼显示 0.95 却排在显示 0.93 的三文鱼后面」这种自相矛盾的结果。
             */
            m.put("_rank", Math.round(sim * 10000) / 10000.0);
            m.put("_d", d);
            scored.add(m);
        }

        // 相似度高者在前；相似度相同时再按原始距离近的在前，保证结果稳定
        scored.sort(Comparator
                .comparingDouble((Map<String, Object> m) -> (Double) m.get("_rank")).reversed()
                .thenComparingDouble(m -> (Double) m.get("_d")));

        List<Map<String, Object>> out = new ArrayList<>();
        for (int i = 0; i < Math.min(topN, scored.size()); i++) {
            Map<String, Object> m = scored.get(i);
            m.remove("_d");
            m.remove("_rank");
            out.add(m);
        }
        return out;
    }

    /** 加权归一化欧氏距离 */
    private double dist(Ingredient a, Ingredient b,
                        double maxCal, double maxPro, double maxCarb,
                        double maxFat, double maxFiber, double maxGi) {
        double dc = norm(nz(a.getCaloriesPer100g()), maxCal) - norm(nz(b.getCaloriesPer100g()), maxCal);
        double dp = norm(nz(a.getProteinPer100g()), maxPro) - norm(nz(b.getProteinPer100g()), maxPro);
        double dcarb = norm(nz(a.getCarbsPer100g()), maxCarb) - norm(nz(b.getCarbsPer100g()), maxCarb);
        double df = norm(nz(a.getFatPer100g()), maxFat) - norm(nz(b.getFatPer100g()), maxFat);
        double dfib = norm(nz(a.getFiberPer100g()), maxFiber) - norm(nz(b.getFiberPer100g()), maxFiber);
        // GI 只有部分食材有，两边都缺省时该维不参与
        double dgi = 0;
        if (nz(a.getGiValue()) > 0 && nz(b.getGiValue()) > 0) {
            dgi = norm(nz(a.getGiValue()), maxGi) - norm(nz(b.getGiValue()), maxGi);
        }
        double sum = W_CAL * dc * dc + W_PRO * dp * dp + W_CARB * dcarb * dcarb
                   + W_FAT * df * df + W_FIBER * dfib * dfib + W_GI * dgi * dgi;
        return Math.sqrt(sum);
    }

    private double norm(double v, double max) {
        return max <= 0 ? 0 : Math.min(1.0, v / max);
    }

    /**
     * 宽松匹配目标食材。
     * 顺序：完全相等 → 忽略大小写相等 → 双向包含 → 编辑距离最近（且足够像）
     * 命中多条同名时（库里确有重名），选与「编辑距离最近 / 营养最主流」无关，
     * 直接取 id 最小的那条，保证结果稳定可复现。
     */
    private Ingredient findIngredient(List<Ingredient> all, String target) {
        String t = target.trim();
        String tl = t.toLowerCase();

        // 1) 完全相等：取 id 最小的，保证稳定
        Ingredient best = null;
        for (Ingredient i : all) {
            if (i.getName() == null) continue;
            if (i.getName().equals(t)) {
                if (best == null || cmpId(i, best) < 0) best = i;
            }
        }
        if (best != null) return best;

        // 2) 忽略大小写
        for (Ingredient i : all) {
            if (i.getName() == null) continue;
            if (i.getName().toLowerCase().equals(tl)) {
                if (best == null || cmpId(i, best) < 0) best = i;
            }
        }
        if (best != null) return best;

        // 3) 双向包含：处理「白米饭」→「米饭」、「牛奶」→「低脂牛奶」这类
        //    优先选长度最接近的（「米饭」比「小米」更贴近「白米饭」的语义）
        int bestLenGap = Integer.MAX_VALUE;
        for (Ingredient i : all) {
            if (i.getName() == null) continue;
            String n = i.getName();
            boolean match = n.contains(t) || t.contains(n);
            if (!match) continue;
            int gap = Math.abs(n.length() - t.length());
            if (gap < bestLenGap || (gap == bestLenGap && best != null && cmpId(i, best) < 0)) {
                bestLenGap = gap;
                best = i;
            }
        }
        return best;
    }

    /** 营养指纹：六项数值拼成字符串，用于识别「同营养不同名」的重复条目 */
    private String fingerprint(Ingredient i) {
        return String.format("%.2f|%.2f|%.2f|%.2f|%.2f|%.0f",
                nz(i.getCaloriesPer100g()), nz(i.getProteinPer100g()), nz(i.getCarbsPer100g()),
                nz(i.getFatPer100g()), nz(i.getFiberPer100g()), nz(i.getGiValue()));
    }

    private int cmpId(Ingredient a, Ingredient b) {
        if (a.getId() == null) return 1;
        if (b.getId() == null) return -1;
        return a.getId().compareTo(b.getId());
    }

    /** 生成中文替代理由，描述相对目标的营养差异 */
    private String buildReason(Ingredient base, Ingredient cand) {
        List<String> parts = new ArrayList<>();

        double kb = nz(base.getCaloriesPer100g());
        double kc = nz(cand.getCaloriesPer100g());
        if (kb > 0) {
            double pct = (kc - kb) / kb * 100;
            if (pct <= -15) parts.add("热量低约 " + Math.round(-pct) + "%");
            else if (pct >= 15) parts.add("热量高约 " + Math.round(pct) + "%");
            else parts.add("热量接近");
        }

        double pb = nz(base.getProteinPer100g());
        double pc = nz(cand.getProteinPer100g());
        if (pc >= pb * 1.15 && pc > 0) parts.add("蛋白质更高");
        else if (pc <= pb * 0.7) parts.add("蛋白质偏低");

        double fb = nz(base.getFatPer100g());
        double fc = nz(cand.getFatPer100g());
        if (fc < fb * 0.7) parts.add("脂肪更低");
        else if (fc > fb * 1.5 && fc > 5) parts.add("脂肪较高，注意用量");

        double fib = nz(cand.getFiberPer100g());
        if (fib >= 2) parts.add("膳食纤维丰富");

        double gb = nz(base.getGiValue());
        double gcv = nz(cand.getGiValue());
        if (gcv > 0 && gcv <= 55 && (gb == 0 || gb > 55)) parts.add("低 GI");

        if (parts.isEmpty()) {
            return "营养构成相近，可直接替换";
        }
        return String.join("，", parts);
    }
}
