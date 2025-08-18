import { useEffect, useState } from 'react';
import authApi from '@/api/auth';
import ConversationTile from './Conversation';
import ConversationMessages from './Conversation/message'
import './index.css'

export const Dashboard = () => {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messagesLoading, setMessagesLoading] = useState(false);

  useEffect(() => {
    const loadConversations = async () => {
      try {
        setLoading(true);
        const response = await authApi.getConversations();
        setConversations(response.data.data || []);
      } catch (err) {
        setError('Failed to load conversations');
        console.error('Error loading conversations:', err);
      } finally {
        setLoading(false);
      }
    };

    loadConversations();
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div>Loading conversations...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <div className="error-text">{error}</div>
      </div>
    );
  }

  const handleClick = async (conversation) => {
    try {
      setMessagesLoading(true);
      setSelectedConversation(conversation);
      const response = await authApi.getMessages(conversation.id);
      setMessages(response?.data?.data || []);
    } catch (err) {
      console.error('Error loading messages:', err);
      setMessages([]);
    } finally {
      setMessagesLoading(false);
    }
  }

  return (
    <>
      <div className="dashboard-container">
        {/* <h1 style={{ marginBottom: '20px' }}>Conversations</h1> */}
        <div className="conversations-list">
          {conversations.length === 0 ? (
            <div className="empty-conversations">
              No conversations found
            </div>
          ) : (
                conversations.map((conversation) => (
                  <ConversationTile
                    key={conversation.id} 
                    conversation={conversation}
                    handleClick={() => handleClick(conversation)}
                  />
                ))
              )}
        </div>
        <ConversationMessages messages={messages} />
      </div>
    </>
  );
};
