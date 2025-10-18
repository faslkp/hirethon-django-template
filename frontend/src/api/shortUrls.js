import apiClient from './client';

export const shortUrlsAPI = {
  list: (params) => apiClient.get('/short-urls/', { params }),
  
  get: (id) => apiClient.get(`/short-urls/${id}/`),
  
  create: (data) => apiClient.post('/short-urls/', data),
  
  update: (id, data) => apiClient.patch(`/short-urls/${id}/`, data),
  
  delete: (id) => apiClient.delete(`/short-urls/${id}/`),
  
  generateQR: (id) => apiClient.post(`/short-urls/${id}/generate_qr/`),
};

