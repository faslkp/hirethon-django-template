import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { bulkUploadAPI } from '../api/bulkUpload';

export const useBulkUploadTasks = () => {
  return useQuery({
    queryKey: ['bulk-upload-tasks'],
    queryFn: async () => {
      const response = await bulkUploadAPI.list();
      return response.data;
    },
  });
};

export const useBulkUploadTask = (id) => {
  return useQuery({
    queryKey: ['bulk-upload-task', id],
    queryFn: async () => {
      const response = await bulkUploadAPI.get(id);
      return response.data;
    },
    enabled: !!id,
    refetchInterval: (data) => {
      // Keep polling if task is still processing
      if (data?.status === 'PROCESSING' || data?.status === 'PENDING') {
        return 2000; // Poll every 2 seconds
      }
      return false; // Stop polling
    },
  });
};

export const useCreateBulkUpload = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (formData) => bulkUploadAPI.create(formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bulk-upload-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['short-urls'] });
    },
  });
};

export const useDownloadBulkUpload = () => {
  return useMutation({
    mutationFn: async (id) => {
      const response = await bulkUploadAPI.download(id);
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `bulk_upload_result_${id}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return response.data;
    },
  });
};

