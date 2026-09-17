import request from '@/utils/request'

export default {
  getNotifications() {
    return request.get('/notification/list')
  },
  markAsRead(id) {
    return request.put(`/notification/read/${id}`)
  },
  deleteNotification(id) {
    return request.put(`/notification/delete/${id}`)
  }
}
