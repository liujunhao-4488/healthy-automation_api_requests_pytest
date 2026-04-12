import axios from '../utils/axios';

export default {
  getConversations() {
    return axios.get('/assistant/conversations');
  },
  createConversation(payload) {
    return axios.post('/assistant/conversations', payload);
  },
  getMessages(conversationId) {
    return axios.get(`/assistant/conversations/${conversationId}/messages`);
  },
  chat(payload) {
    return axios.post('/assistant/chat', payload, { timeout: 60000 });
  },
  deleteConversation(conversationId) {
    return axios.delete(`/assistant/conversations/${conversationId}`);
  }
};
