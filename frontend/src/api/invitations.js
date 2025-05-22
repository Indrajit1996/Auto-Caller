import { API_ROUTES } from '@/constants/apiConstants';

import api from './index';

const invitationsApi = {
  getInvitationsDataTable: (requestBody) => {
    return api.post(API_ROUTES.INVITATIONS.INVITATIONS_DATATABLE, requestBody);
  },

  createInvitation: (data) => {
    return api.post(API_ROUTES.INVITATIONS.CREATE_INVITATION, data);
  },

  getInvitationTypeCounts: () => {
    return api.get(API_ROUTES.INVITATIONS.INVITATION_TYPE_COUNTS);
  },

  resendInvitation: (id) => {
    return api.post(API_ROUTES.INVITATIONS.RESEND_INVITATION(id));
  },

  deactivateInvitation: (id) => {
    return api.patch(API_ROUTES.INVITATIONS.DEACTIVATE_INIVITATION(id));
  },

  getInvitation: (id) => {
    return api.get(API_ROUTES.INVITATIONS.GET_INVITATION(id));
  },

  getInvitationByToken: (token) => {
    return api.get(API_ROUTES.INVITATIONS.GET_INVITATION_BY_TOKEN(token));
  },
};

export default invitationsApi;
