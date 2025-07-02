import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

const STORE_NAME = 'conversation-store';

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
      }
    }),
    {
      name: STORE_NAME,
      storage: createJSONStorage(() => localStorage),
    }
  )
);

export default useConversationStore; 