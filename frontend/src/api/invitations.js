import apiClient from './client';

export const invitationsAPI = {
  get: (token) => apiClient.get(`/invitations/get/?token=${token}`),
  
  accept: (token) => apiClient.post('/invitations/accept/', { token }),
};

