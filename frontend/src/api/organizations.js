import apiClient from './client';

export const organizationsAPI = {
  list: () => apiClient.get('/organizations/'),
  
  get: (id) => apiClient.get(`/organizations/${id}/`),
  
  create: (data) => apiClient.post('/organizations/', data),
  
  update: (id, data) => apiClient.patch(`/organizations/${id}/`, data),
  
  delete: (id) => apiClient.delete(`/organizations/${id}/`),
  
  invite: (id, data) => apiClient.post(`/organizations/${id}/invite/`, data),
  
  members: (id) => apiClient.get(`/organizations/${id}/members/`),
  
  removeMember: (id, userId) => 
    apiClient.delete(`/organizations/${id}/remove_member/`, { data: { user_id: userId } }),
  
  // Invitation management
  invitations: (id) => apiClient.get(`/organizations/${id}/invitations/`),
  
  cancelInvitation: (id, invitationId) => 
    apiClient.post(`/organizations/${id}/cancel_invitation/`, { invitation_id: invitationId }),
};

