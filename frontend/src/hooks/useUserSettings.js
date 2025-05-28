import userSettingsStore from '@/store/userSettingsStore';

const useUserSettings = () => {
  const { userSettings, setSidebarCollapsed, getSidebarCollapsed } = userSettingsStore();

  return {
    userSettings,
    sidebarCollapsed: getSidebarCollapsed(),
    setSidebarCollapsed: (collapsed) => {
      setSidebarCollapsed(collapsed);
    },
  };
};

export default useUserSettings;
