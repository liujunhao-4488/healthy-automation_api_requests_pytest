import axios from '../utils/axios';

const notificationApi = {
  getNotifications: () => axios.get('/notification/list'),
  markAsRead: (id) => axios.put(`/notification/read/${id}`),
  deleteNotification: (id) => axios.put(`/notification/delete/${id}`),
  publishNotification: (payload) => axios.post('/notification/admin/publish', payload)
};

export default notificationApi;
