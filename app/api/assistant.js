import request from '@/utils/request'

export default {
  getConversations() {
    return request.get('/assistant/conversations')
  },
  createConversation(payload) {
    return request.post('/assistant/conversations', payload)
  },
  getMessages(conversationId) {
    return request.get(`/assistant/conversations/${conversationId}/messages`)
  },
  chat(payload) {
    return request.post('/assistant/chat', payload, { timeout: 60000 })
  },
  deleteConversation(conversationId) {
    return request.delete(`/assistant/conversations/${conversationId}`)
  }
}
