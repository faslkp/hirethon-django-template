import { useQuery, useMutation } from '@tanstack/react-query';
import { invitationsAPI } from '../api/invitations';

export const useGetInvitation = (token) => {
  return useQuery({
    queryKey: ['invitation', token],
    queryFn: async () => {
      const response = await invitationsAPI.get(token);
      return response.data;
    },
    enabled: !!token,
    retry: false,
  });
};

export const useAcceptInvitation = () => {
  return useMutation({
    mutationFn: (token) => invitationsAPI.accept(token),
  });
};

