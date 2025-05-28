import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

import authApi from '@/api/auth';
import { retry } from '@/utils/api';

const STORE_NAME = 'auth-storage';

const initialState = {
  token: null,
  is_token_active: false,
  isLoading: false,
  user: null,
  pendingEmailVerificationEmail: null, // Add this property to store email pending verification
};

const authStore = create(
  persist(
    (set, get) => ({
      // State
      ...initialState,

      // Computed Properties
      isSuperUser: () => get().user?.is_superuser ?? false,

      fetchUserData: async () => {
        try {
          const { data: userData } = await retry(async () => await authApi.getMe(), 3, 1000);
          set({ user: userData });
          return userData;
        } catch (error) {
          get().logout();
          throw error;
        }
      },

      // Session Management
      initializeAuth: async () => {
        set({ isLoading: true });
        try {
          const token = get().token;
          if (!token) {
            get().logout();
            return;
          }
          await get().fetchUserData();
          set({ is_token_active: true });
        } catch (error) {
          get().logout();
        } finally {
          set({ isLoading: false });
        }
      },

      login: async (credentials) => {
        set({ isLoading: true });
        try {
          const {
            data: { access_token },
          } = await authApi.getAccessToken(credentials);
          set({ token: access_token });
          await get().fetchUserData();
          set({ is_token_active: true });
        } finally {
          set({ isLoading: false });
        }
      },

      logout: () => {
        // reset to initial state
        set({ ...initialState });
      },

      // User Management
      updateUserName: ({ first_name, last_name }) => {
        set((state) => ({
          user: {
            ...state.user,
            first_name,
            last_name,
          },
        }));
      },

      setPendingEmailVerificationEmail: (email) => {
        set({ pendingEmailVerificationEmail: email });
      },
      clearPendingEmailVerificationEmail: () => {
        set({ pendingEmailVerificationEmail: null });
      },
    }),
    {
      name: STORE_NAME,
      storage: createJSONStorage(() => localStorage),
    }
  )
);

export default authStore;
