import { getToken } from './storage'

// Phone/emulator debugging must use the computer LAN IP instead of 127.0.0.1.
// If the computer IP changes, update this value accordingly.
export const BASE_URL = 'http://192.168.1.3:8080/api'
let unauthorizedHandler = null

export const setUnauthorizedHandler = (handler) => {
  unauthorizedHandler = handler
}

const mergeHeaders = (headers = {}) => {
  const token = getToken()
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...headers
  }
}

export const request = ({ url, method = 'GET', data, header, timeout = 10000 }) => {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      timeout,
      header: mergeHeaders(header),
      success: (response) => {
        const { statusCode, data: body } = response

        if (statusCode === 401) {
          unauthorizedHandler && unauthorizedHandler()
          reject(new Error(body?.message || '登录状态已失效'))
          return
        }

        if (statusCode >= 200 && statusCode < 300) {
          resolve(body)
          return
        }

        reject(new Error(body?.message || '请求失败'))
      },
      fail: (error) => {
        reject(new Error(error?.errMsg || '网络请求失败'))
      }
    })
  })
}

export default {
  get(url, params, options = {}) {
    return request({ url, method: 'GET', data: params, ...options })
  },
  post(url, data, options = {}) {
    return request({ url, method: 'POST', data, ...options })
  },
  put(url, data, options = {}) {
    return request({ url, method: 'PUT', data, ...options })
  },
  delete(url, data, options = {}) {
    return request({ url, method: 'DELETE', data, ...options })
  }
}
