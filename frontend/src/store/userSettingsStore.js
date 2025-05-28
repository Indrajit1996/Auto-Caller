import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

const STORE_NAME = 'user-settings';

const initialState = {
  userSettings: {
    sidebarCollapsed: false,
  },
};

const userSettingsStore = create(
  persist(
    (set, get) => ({
      userSettings: initialState.userSettings,
      setSidebarCollapsed: (collapsed) =>
        set((state) => ({
          userSettings: {
            ...state.userSettings,
            sidebarCollapsed: collapsed,
          },
        })),
      getSidebarCollapsed: () => get().userSettings.sidebarCollapsed,
    }),
    {
      name: STORE_NAME,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ userSettings: state.userSettings }),
    }
  )
);

export default userSettingsStore;
