package com.health.dto;

import lombok.Data;
import javax.validation.constraints.DecimalMax;
import javax.validation.constraints.DecimalMin;
import javax.validation.constraints.Max;
import javax.validation.constraints.Min;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Pattern;

/**
 * 健康档案请求体。
 *
 * 【数值范围校验的两条设计原则】
 *
 * 1. 范围取"人体学上不可能越过的宽边界"，作用是拦住 0 / 负数 / 明显离谱的量级
 *    （脏数据、脚本误传、前端算错），**不是**做严格的业务准入——
 *    那属于产品规则，会随运营策略调整，不该固化在参数校验里。
 *
 * 2. age 是 Integer，用 @Min/@Max；height / weight / bloodSugar 是 Double，
 *    **必须用 @DecimalMin/@DecimalMax**。原因：@Min/@Max 只支持
 *    整数系类型（byte/short/int/long + 包装类，以及 BigInteger/BigDecimal），
 *    挂在 Double 上会抛 UnexpectedTypeException——这是很容易踩的坑。
 *
 * 3. 范围注解对 null 一律放行（Bean Validation 规范行为），
 *    "必填"由 @NotNull 负责，两件事不重复管。
 *
 * 4. 同一字段的上下限共用一条 message：如果写成"至少50"和"最多250"两句，
 *    调用方拿到的具体是哪句取决于校验器的执行顺序，不可控。
 *
 * 5. 定范围前核对过库里的存量数据（含 120 条模拟用户），
 *    确保新规则不会把已有的合法记录变成"非法"——否则那些用户下次改档案会被拦死。
 */
@Data
public class HealthInfoDTO {

    @NotNull(message = "年龄不能为空")
    @Min(value = 1, message = "年龄需在 1~150 岁之间")
    @Max(value = 150, message = "年龄需在 1~150 岁之间")
    private Integer age;

    /**
     * 性别取值统一为 male / female（英文小写，2026-09-20 归一）。
     *
     * 为什么要收窄：这个字段落库的字面值**同时是 BMR 公式的分支开关**
     * （见 HealthInfoServiceImpl.calculateBMR 里的 "male".equalsIgnoreCase）。
     * 取值写错不会报任何错，只会让 BMR 静默走错公式，再被拿去算 TDEE 和目标热量。
     * 归一前库里三套取值并存：male 83 / female 98 / 男 3。
     *
     * 界面文案「男」「女」由前端 radio 的 label 负责，发到后端的是 value
     * （male / female）——显示文案和传输值是两回事，别混。
     */
    @NotBlank(message = "性别不能为空")
    @Pattern(regexp = "male|female", message = "性别取值不合法，只能是 male 或 female")
    private String gender;

    /**
     * 身高下限 50cm 不只是"取值范围"：
     * BMI 计算里 height 被当成除数（bmi = weight / (height/100)^2），
     * height=0 会算出 Infinity，最终在入库时炸出 MyBatis/MySQL 异常栈并原样返回给客户端。
     * 在这里拦掉，既修了数据问题，也堵住了内部实现泄露。
     */
    @NotNull(message = "身高不能为空")
    @DecimalMin(value = "50", message = "身高需在 50~250cm 之间")
    @DecimalMax(value = "250", message = "身高需在 50~250cm 之间")
    private Double height;

    @NotNull(message = "体重不能为空")
    @DecimalMin(value = "10", message = "体重需在 10~500kg 之间")
    @DecimalMax(value = "500", message = "体重需在 10~500kg 之间")
    private Double weight;

    private Double bmi;
    private Double bmr;
    private String bloodPressure;

    /** inclusive = false 表示"大于 0"而不是"大于等于 0"：血糖 0 不是有效值。 */
    @DecimalMin(value = "0", inclusive = false, message = "血糖需在 0~50mmol/L 之间")
    @DecimalMax(value = "50", message = "血糖需在 0~50mmol/L 之间")
    private Double bloodSugar;

    private String activityLevel;
    private Integer exerciseDuration;
    private String exerciseType;
    private String chronicDiseases;

}
