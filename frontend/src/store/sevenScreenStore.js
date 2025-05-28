import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

const STORE_NAME = 'seven-screen-settings';

const initialState = {
  isHorizontal: true,
  currentScreen: 1,
};

const sevenScreenStore = create(
  persist(
    (set, get) => ({
      settings: initialState,
      setIsHorizontal: (isHorizontal) =>
        set((state) => ({
          settings: {
            ...state.settings,
            isHorizontal,
          },
        })),
      setCurrentScreen: (currentScreen) =>
        set((state) => ({
          settings: {
            ...state.settings,
            currentScreen,
          },
        })),
      getIsHorizontal: () => get().settings.isHorizontal,
      getCurrentScreen: () => get().settings.currentScreen,
    }),
    {
      name: STORE_NAME,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ settings: state.settings }),
    }
  )
);

export default sevenScreenStore;
