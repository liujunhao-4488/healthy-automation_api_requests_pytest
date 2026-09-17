const pad = (value) => String(value).padStart(2, '0')

export const formatDate = (value = new Date()) => {
  const date = value instanceof Date ? value : new Date(value)
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export const formatTime = (value = new Date()) => {
  const date = value instanceof Date ? value : new Date(value)
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export const formatDateTime = (value) => {
  if (!value) {
    return ''
  }
  const date = value instanceof Date ? value : new Date(value)
  return `${formatDate(date)} ${formatTime(date)}`
}

export const toNumber = (value, fallback = 0) => {
  const result = Number(value)
  return Number.isFinite(result) ? result : fallback
}

export const groupBy = (list = [], key) => {
  return (Array.isArray(list) ? list : []).reduce((acc, item) => {
    const groupKey = typeof key === 'function' ? key(item) : item?.[key]
    if (!acc[groupKey]) {
      acc[groupKey] = []
    }
    acc[groupKey].push(item)
    return acc
  }, {})
}
