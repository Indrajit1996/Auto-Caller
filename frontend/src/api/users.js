import { API_ROUTES } from '@/constants/apiConstants';

import api from './index';

const usersApi = {
  getUsersDataTable: (requestBody) => {
    return api.post(API_ROUTES.USERS.USERS_DATATABLE, requestBody);
  },

  getUser: (id) => {
    return api.get(API_ROUTES.USERS.USER(id));
  },

  addUser: (credentials) => {
    return api.post(API_ROUTES.USERS.ADD_USER, credentials);
  },

  editUser: (id, credentials) => {
    return api.patch(API_ROUTES.USERS.USER(id), credentials);
  },

  updateStatus: (id, status) => {
    return api.patch(API_ROUTES.USERS.UPDATE_STATUS(id), { status });
  },

  getUserStatusCounts: () => {
    return api.get(API_ROUTES.USERS.STAUTS_COUNTS);
  },

  exportUserData: () => {
    return api.get(API_ROUTES.USERS.EXPORT_USER_DATA);
  },
};

export default usersApi;
