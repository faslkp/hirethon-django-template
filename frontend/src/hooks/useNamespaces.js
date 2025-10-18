import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { namespacesAPI } from '../api/namespaces';

export const useNamespaces = () => {
  return useQuery({
    queryKey: ['namespaces'],
    queryFn: async () => {
      const response = await namespacesAPI.list();
      return response.data;
    },
  });
};

export const useNamespace = (id) => {
  return useQuery({
    queryKey: ['namespace', id],
    queryFn: async () => {
      const response = await namespacesAPI.get(id);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useCreateNamespace = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data) => namespacesAPI.create(data),
    onSuccess: () => {
      // Invalidate both namespaces and organizations queries
      queryClient.invalidateQueries({ queryKey: ['namespaces'] });
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
    },
  });
};

export const useDeleteNamespace = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id) => namespacesAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['namespaces'] });
    },
  });
};

