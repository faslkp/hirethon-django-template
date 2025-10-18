import apiClient from './client';

export const namespacesAPI = {
  list: () => apiClient.get('/namespaces/'),
  
  get: (id) => apiClient.get(`/namespaces/${id}/`),
  
  create: (data) => apiClient.post('/namespaces/', data),
  
  delete: (id) => apiClient.delete(`/namespaces/${id}/`),
};

