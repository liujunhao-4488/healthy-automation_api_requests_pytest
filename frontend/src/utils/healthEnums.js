// 健康档案里「枚举字段」的字典与判定工具。
//
// 【约定 · 2026-09-20 gender 归一】
//   库里 / 网络上统一用英文小写：male | female
//   界面上仍然显示中文：「男」「女」
//
//   关键点：**显示文案和传输值是两回事**。
//   el-radio 的 value 是发到后端的数据，标签里的文字只是给用户看的。
//   所以「前端传男女」这个说法本身就不成立——用户点的是「男」，
//   发出去的是 value（现在改成 male），用户完全无感。
//
// 【为什么要收窄取值】
//   gender 落库的那个字面值**同时是 BMR 公式的分支开关**
//   （后端 HealthInfoServiceImpl.calculateBMR 里用 "male".equalsIgnoreCase 判断）。
//   取值写错不会报任何错，只会静默走错公式、算出一个错的 BMR，
//   再被拿去算 TDEE 和目标热量。归一前库里三套值并存：male 83 / female 98 / 男 3。

export const GENDER_OPTIONS = [
  { value: 'male', label: '男' },
  { value: 'female', label: '女' }
];

/**
 * 把库里的 gender 转成界面文案。
 * 遇到字典外的值时**原样返回**，不偷偷替换成「--」——
 * 异常数据应该看得见，而不是被前端抹平。
 */
export const genderLabel = (value) => {
  const hit = GENDER_OPTIONS.find((item) => item.value === value);
  return hit ? hit.label : value || '--';
};

/**
 * 是否男性。
 * 读取侧故意保持宽容：兼容历史中文值和大小写（male / MALE / 男），
 * 这样即使库里有没迁干净的旧值，也不会算错公式。
 * 写入侧（radio）只发 male / female，源头保证干净。
 */
export const isMaleGender = (value) => {
  const normalized = String(value ?? '').trim().toLowerCase();
  return normalized === 'male' || normalized === '男';
};
