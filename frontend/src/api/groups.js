import { API_ROUTES } from '@/constants/apiConstants';

import api from '.';

const groupsApi = {
  getGroupsDataTable: (requestBody) => api.post(API_ROUTES.GROUPS.GROUPS_DATATABLE, requestBody),
  getGroup: (groupId) => api.get(API_ROUTES.GROUPS.GET_GROUPS + `/${groupId}`),
  getGroups: () => api.get(API_ROUTES.GROUPS.GET_GROUPS + '/'),
  getGroupUsers: (params) => api.post(API_ROUTES.GROUPS.GET_GROUP_USERS, params),
  removeUserFromGroup: ({ groupId, userId }) =>
    api.delete(API_ROUTES.GROUPS.REMOVE_USER_FROM_GROUP({ groupId, userId })),
  getAvailableUsers: (params) => api.post('/users/datatable', params),
  addUsersToGroup: (groupId, userIds) =>
    api.post(`/groups/${groupId}/users`, { user_ids: userIds }),
  createGroup: (data) => api.post('/groups/', data),
  updateGroup: (groupId, data) => api.patch(`/groups/${groupId}`, data),
  deleteGroup: ({ group_id }) => api.delete(`/groups/${group_id}`),
};

export default groupsApi;
