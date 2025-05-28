export const ROUTES = Object.freeze({
  LANDING_PAGE: '/',
  AUTH: {
    LOGIN: '/',
    REGISTER: '/register',
    RESET_PASSWORD: '/reset-password',
    VERIFY_EMAIL: '/verify-email',
    FORGOT_PASSWORD: '/forgot-password',
  },
  LOGGED_IN_HOME: '/dashboard',
  ADMIN: {
    USERS: '/admin/users',
    USERS_DETAIL: '/admin/users/:userId',
    INVITES: '/admin/invites',
    GROUPS: '/admin/groups',
    GROUP_DETAIL: '/admin/groups/:groupId',
  },
  PROFILE: '/profile',
});
