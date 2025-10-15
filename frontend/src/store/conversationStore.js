import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import api from '@/api';

const STORE_NAME = 'conversation-store-1';

const initialConversations = {
  1: [],
  2: [],
};

const useConversationStore = create(
  persist(
    (set, get) => ({
      // State
      conversations: initialConversations,
      history: [], // Array of { userId, conversation, closedAt }
      sessions: [],
      loading: false,

      // Actions
      setConversations: (conversationsOrUpdater) => {
        if (typeof conversationsOrUpdater === 'function') {
          set((state) => ({ conversations: conversationsOrUpdater(state.conversations) }));
        } else {
          set({ conversations: conversationsOrUpdater });
        }
      },
      
      addHistory: (item) =>
        set((state) => ({
          history: [item, ...state.history].slice(0, 5),
        })),

      addMessageWithAudio: (userId, message, audioUrl = null) => {
        const currentConversations = get().conversations;
        const userConversations = currentConversations[userId] || [];
        
        set({
          conversations: {
            ...currentConversations,
            [userId]: [
              ...userConversations,
              {
                sender: 'user',
                text: message,
                audioUrl: audioUrl,
                timestamp: Date.now(),
              },
            ],
          },
        });
      },

      removeHistory: (idx) =>
        set((state) => ({
          history: state.history.filter((_, i) => i !== idx),
        })),
        
      clearConversationsForUser: (userId) => {
        const currentConversations = get().conversations;
        set({
          conversations: {
            ...currentConversations,
            [userId]: [],
          },
        });
      },

      restoreFromHistory: (idx) => {
        const historyItem = get().history[idx];
        if (!historyItem) return;

        const currentConversations = get().conversations;

        set({
          conversations: {
            ...currentConversations,
            [historyItem.userId]: historyItem.conversation,
          },
        });

        // Remove from history after restoring
        get().removeHistory(idx);
        return historyItem.userId;
      },

      fetchRecentSessions: async () => {
        set({ loading: true });
        try {
          const res = await api.getRecentCallInteractions();
          if (res.data && res.data.sessions) {
            set({ sessions: res.data.sessions, loading: false });
          } else {
            set({ loading: false });
          }
        } catch (error) {
          console.error('Error fetching recent sessions:', error);
          set({ loading: false });
        }
      }
    }),
    // {
    //   name: STORE_NAME,
    //   storage: createJSONStorage(() => localStorage),
    // }
  )
);

export default useConversationStore; 