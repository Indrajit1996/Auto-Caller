import { API_ROUTES } from '@/constants/apiConstants';

import api from './index';

const notificationsApi = {
  getNotifications: (offset = 0, limit = 100) => {
    return api
      .get(`${API_ROUTES.NOTIFICATIONS.BASE}/?offset=${offset}&limit=${limit}`)
      .then((response) => response.data);
  },

  getNotification: (id) => {
    return api.get(`${API_ROUTES.NOTIFICATIONS.BASE}/${id}`).then((response) => response.data);
  },

  markAsRead: (id) => {
    return api
      .patch(`${API_ROUTES.NOTIFICATIONS.BASE}/${id}/read`)
      .then((response) => response.data);
  },

  markAllAsRead: () => {
    return api.patch(`${API_ROUTES.NOTIFICATIONS.BASE}/read-all`).then((response) => response.data);
  },
};

export default notificationsApi;
