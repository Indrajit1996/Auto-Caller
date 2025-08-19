import { apiClient } from './index';

export const conversationsApi = {
  // Get all conversations
  getConversations: (params = {}) => {
    return apiClient.get('/conversations', { params });
  },

  // Get a specific conversation with messages
  getConversation: (conversationId) => {
    return apiClient.get(`/conversations/${conversationId}`);
  },

  // Create a new conversation
  createConversation: (conversationData) => {
    return apiClient.post('/conversations', conversationData);
  },

  // Update a conversation (e.g., add audio URL)
  updateConversation: (conversationId, updateData) => {
    return apiClient.put(`/conversations/${conversationId}`, updateData);
  },

  // Get messages for a conversation
  getMessages: (conversationId) => {
    return apiClient.get(`/conversations/${conversationId}/messages`);
  },

  // Add a message to a conversation
  createMessage: (conversationId, messageData) => {
    return apiClient.post(`/conversations/${conversationId}/messages`, messageData);
  },

  // Update a message (e.g., add audio URL)
  updateMessage: (messageId, updateData) => {
    return apiClient.put(`/conversations/messages/${messageId}`, updateData);
  }
}; 