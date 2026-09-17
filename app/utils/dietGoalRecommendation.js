const KG_TO_KCAL = 7700
const DEFAULT_PLAN_DAYS = 84

export const goalProfiles = {
  fat_loss: { calorieFactor: 1, proteinRatio: 32, carbsRatio: 38, fatRatio: 30, waterTarget: 2500, defaultAdjustment: -350, minAdjustment: -900, maxAdjustment: -200 },
  muscle_toning: { calorieFactor: 1, proteinRatio: 35, carbsRatio: 40, fatRatio: 25, waterTarget: 3000, defaultAdjustment: 220, minAdjustment: 80, maxAdjustment: 420 },
  weight_maintenance: { calorieFactor: 1, proteinRatio: 25, carbsRatio: 45, fatRatio: 30, waterTarget: 2200, defaultAdjustment: 0, minAdjustment: -100, maxAdjustment: 100 },
  healthy_weight_gain: { calorieFactor: 1, proteinRatio: 24, carbsRatio: 48, fatRatio: 28, waterTarget: 2600, defaultAdjustment: 320, minAdjustment: 180, maxAdjustment: 700 },
  blood_sugar_control: { calorieFactor: 0.95, proteinRatio: 30, carbsRatio: 35, fatRatio: 35, waterTarget: 2200, defaultAdjustment: -120, minAdjustment: -300, maxAdjustment: 120 },
  lipid_control: { calorieFactor: 0.96, proteinRatio: 28, carbsRatio: 42, fatRatio: 30, waterTarget: 2300, defaultAdjustment: -150, minAdjustment: -320, maxAdjustment: 100 },
  low_sodium: { calorieFactor: 0.98, proteinRatio: 27, carbsRatio: 43, fatRatio: 30, waterTarget: 2400, defaultAdjustment: -80, minAdjustment: -200, maxAdjustment: 100 },
  pregnancy_nutrition: { calorieFactor: 1.08, proteinRatio: 27, carbsRatio: 48, fatRatio: 25, waterTarget: 2800, defaultAdjustment: 260, minAdjustment: 150, maxAdjustment: 420 },
  child_growth: { calorieFactor: 1.05, proteinRatio: 22, carbsRatio: 53, fatRatio: 25, waterTarget: 1800, defaultAdjustment: 180, minAdjustment: 100, maxAdjustment: 350 },
  senior_wellness: { calorieFactor: 0.96, proteinRatio: 30, carbsRatio: 42, fatRatio: 28, waterTarget: 2100, defaultAdjustment: -60, minAdjustment: -180, maxAdjustment: 120 }
}

const clamp = (value, min, max) => Math.min(Math.max(value, min), max)

const parseDate = (value) => {
  if (!value) return null
  if (value instanceof Date) return value
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

const getPlanDays = (startDate, endDate) => {
  const start = parseDate(startDate)
  const end = parseDate(endDate)
  if (!start || !end) return DEFAULT_PLAN_DAYS
  const diff = Math.ceil((end - start) / (1000 * 60 * 60 * 24))
  return Math.max(diff, 1)
}

export const calculateBmrByHealthInfo = (healthInfo) => {
  if (!healthInfo?.height || !healthInfo?.weight || !healthInfo?.age) return 0

  if (healthInfo.gender === '男' || healthInfo.gender === 'male') {
    return Math.round(88.362 + 13.397 * healthInfo.weight + 4.799 * healthInfo.height - 5.677 * healthInfo.age)
  }

  return Math.round(447.593 + 9.247 * healthInfo.weight + 3.098 * healthInfo.height - 4.33 * healthInfo.age)
}

const buildAdvice = ({ goalType, weightDelta, planDays, dailyAdjustment, targetWeightUsed }) => {
  if (!targetWeightUsed) return '未填写目标体重时，系统会按该目标类型的常规推荐策略生成参考热量。'
  if (goalType === 'weight_maintenance') return '维持体重模式下，系统默认按当前体重附近波动来推荐热量。'

  const absChange = Math.abs(weightDelta || 0)
  const weeklyChange = planDays ? (absChange / planDays) * 7 : 0

  if (goalType === 'fat_loss' && weeklyChange > 1) {
    return '当前减重速度偏快，建议适当延长周期，避免每日热量缺口过大。'
  }

  if ((goalType === 'healthy_weight_gain' || goalType === 'muscle_toning') && weeklyChange > 0.8) {
    return '当前增重速度偏快，建议适当延长周期，让体重变化更平稳。'
  }

  if (Math.abs(dailyAdjustment || 0) < 80) {
    return '当前目标与现状较接近，系统推荐以平稳调整和长期坚持为主。'
  }

  return '系统已结合目标体重与计划周期生成热量调整值，你也可以按实际执行情况再微调。'
}

export const computeDietGoalRecommendation = ({ healthInfo, goalForm }) => {
  if (!healthInfo || !goalForm?.goalType) return null

  const profile = goalProfiles[goalForm.goalType]
  if (!profile) return null

  const currentWeight = Number(healthInfo.weight || 0)
  const bmr = healthInfo.bmr || calculateBmrByHealthInfo(healthInfo)
  const activityMultiplier = {
    sedentary: 1.2,
    lightly_active: 1.375,
    moderately_active: 1.55,
    very_active: 1.725,
    extra_active: 1.9
  }

  const planDays = getPlanDays(goalForm.startDate, goalForm.endDate)
  const estimatedTdee = bmr * (activityMultiplier[healthInfo.activityLevel] || 1.2) * profile.calorieFactor
  const goalType = goalForm.goalType

  let targetWeight = goalForm.targetWeight ? Number(goalForm.targetWeight) : null
  let targetWeightUsed = true

  if (!targetWeight && goalForm.goalType === 'weight_maintenance') {
    targetWeight = currentWeight
  }

  let dailyAdjustment = profile.defaultAdjustment
  let weightDelta = null

  if (targetWeight && currentWeight) {
    weightDelta = Number((targetWeight - currentWeight).toFixed(1))
    const calculatedAdjustment = (weightDelta * KG_TO_KCAL) / planDays
    dailyAdjustment = clamp(calculatedAdjustment, profile.minAdjustment, profile.maxAdjustment)
  } else {
    targetWeightUsed = false
  }

  const targetCalories = Math.round(Math.max(800, estimatedTdee + dailyAdjustment))

  return {
    currentWeight,
    recommendedGoal: {
      targetCalories,
      proteinRatio: profile.proteinRatio,
      carbsRatio: profile.carbsRatio,
      fatRatio: profile.fatRatio,
      proteinTarget: Math.round((targetCalories * (profile.proteinRatio / 100)) / 4),
      carbsTarget: Math.round((targetCalories * (profile.carbsRatio / 100)) / 4),
      fatTarget: Math.round((targetCalories * (profile.fatRatio / 100)) / 9),
      waterTarget: profile.waterTarget
    },
    recommendationContext: {
      targetWeight,
      targetWeightUsed,
      planDays,
      weightDelta,
      dailyAdjustment: Math.round(dailyAdjustment),
      estimatedTdee: Math.round(estimatedTdee),
      advice: buildAdvice({ goalType, weightDelta, planDays, dailyAdjustment, targetWeightUsed })
    }
  }
}

export const formatGoalDate = (date) => {
  if (!date) return null
  if (typeof date === 'string') return date
  const target = new Date(date)
  return `${target.getFullYear()}-${String(target.getMonth() + 1).padStart(2, '0')}-${String(target.getDate()).padStart(2, '0')}`
}

export const formatGoalTime = (time) => {
  if (!time) return null
  if (typeof time === 'string') return time
  const target = new Date(time)
  return `${String(target.getHours()).padStart(2, '0')}:${String(target.getMinutes()).padStart(2, '0')}:00`
}
