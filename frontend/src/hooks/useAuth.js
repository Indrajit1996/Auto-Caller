import authStore from '@/store/authStore';

const useAuth = () => {
  const {
    // State
    token,
    is_token_active,
    user,
    isLoading,
    pendingEmailVerificationEmail,

    // Actions
    login,
    logout,
    initializeAuth,
    updateUserName,
    isSuperUser,
    setPendingEmailVerificationEmail,
  } = authStore();

  const isAuthenticated = Boolean(token && is_token_active);

  return {
    // Auth State
    token,
    is_token_active,
    user,
    isLoading,
    isAuthenticated,
    isSuperUser: isSuperUser(),
    pendingEmailVerificationEmail,

    // Auth Actions
    login,
    logout,
    initializeAuth,
    setPendingEmailVerificationEmail,

    // User Management
    updateUserName,
  };
};

export default useAuth;
