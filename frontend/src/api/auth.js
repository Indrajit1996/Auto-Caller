import { API_ROUTES } from '@/constants/apiConstants';

import api from './index';

const authApi = {
  getAccessToken: (credentials) => api.post(API_ROUTES.AUTH.LOGIN, credentials),
  testToken: () => api.post(API_ROUTES.AUTH.TEST_TOKEN),
  passwordRecovery: (email) => api.post(API_ROUTES.AUTH.PASSWORD_RECOVERY(email)),
  resetPassword: (data) => api.post(API_ROUTES.AUTH.RESET_PASSWORD, data),
  verifyEmail: (token) => api.get(API_ROUTES.AUTH.VERIFY_EMAIL(token)),
  resendVerificationEmail: (email) => {
    return api.post(API_ROUTES.AUTH.RESEND_VERIFICATION_EMAIL, { email });
  },
  registerUser: (data) => api.post(API_ROUTES.AUTH.REGISTER_USER, data),
  getMe: () => api.get(API_ROUTES.AUTH.GET_ME),
  deactivateAccount: () => api.patch(API_ROUTES.AUTH.DEACTIVATE_ACCOUNT),
  updatePassword: (passwordData) => api.patch(API_ROUTES.AUTH.UPDATE_PASSWORD, passwordData),
  updateProfile: (settings) => api.patch(API_ROUTES.AUTH.GET_ME, settings),
};
export default authApi;
