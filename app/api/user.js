import request from '@/utils/request'

export default {
  getProfile() {
    return request.get('/user/profile')
  },
  updateProfile(profile) {
    return request.put('/user/profile', profile)
  },
  getDietPreference() {
    return request.get('/user/diet-preference')
  },
  updateDietPreference(preference) {
    return request.put('/user/diet-preference', preference)
  }
}
