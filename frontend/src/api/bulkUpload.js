import apiClient from './client';

export const bulkUploadAPI = {
  list: () => apiClient.get('/bulk-upload/'),
  
  get: (id) => apiClient.get(`/bulk-upload/${id}/`),
  
  create: (formData) => 
    apiClient.post('/bulk-upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
  
  download: (id) => 
    apiClient.get(`/bulk-upload/${id}/download/`, {
      responseType: 'blob',
    }),
};

