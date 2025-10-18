import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { shortUrlsAPI } from '../api/shortUrls';

export const useShortUrls = (params) => {
  return useQuery({
    queryKey: ['short-urls', params],
    queryFn: async () => {
      const response = await shortUrlsAPI.list(params);
      return response.data;
    },
  });
};

export const useShortUrl = (id) => {
  return useQuery({
    queryKey: ['short-url', id],
    queryFn: async () => {
      const response = await shortUrlsAPI.get(id);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useCreateShortUrl = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data) => shortUrlsAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['short-urls'] });
    },
  });
};

export const useUpdateShortUrl = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }) => shortUrlsAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['short-urls'] });
    },
  });
};

export const useDeleteShortUrl = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id) => shortUrlsAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['short-urls'] });
    },
  });
};

export const useGenerateQR = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id) => shortUrlsAPI.generateQR(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['short-urls'] });
    },
  });
};

