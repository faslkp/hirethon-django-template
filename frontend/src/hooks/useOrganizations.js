import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { organizationsAPI } from '../api/organizations';

export const useOrganizations = () => {
  return useQuery({
    queryKey: ['organizations'],
    queryFn: async () => {
      const response = await organizationsAPI.list();
      return response.data;
    },
  });
};

export const useOrganization = (id) => {
  return useQuery({
    queryKey: ['organization', id],
    queryFn: async () => {
      const response = await organizationsAPI.get(id);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useCreateOrganization = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data) => organizationsAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
    },
  });
};

export const useUpdateOrganization = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }) => organizationsAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
    },
  });
};

export const useDeleteOrganization = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id) => organizationsAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
    },
  });
};

export const useInviteMember = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ orgId, data }) => organizationsAPI.invite(orgId, data),
    onSuccess: (_, variables) => {
      // Invalidate all related queries to refresh the UI
      queryClient.invalidateQueries({ queryKey: ['organization', variables.orgId] });
      queryClient.invalidateQueries({ queryKey: ['organization-members', variables.orgId] });
      queryClient.invalidateQueries({ queryKey: ['organization-invitations', variables.orgId] });
    },
  });
};

export const useOrganizationMembers = (orgId) => {
  return useQuery({
    queryKey: ['organization-members', orgId],
    queryFn: async () => {
      const response = await organizationsAPI.members(orgId);
      return response.data;
    },
    enabled: !!orgId,
  });
};

export const useOrganizationInvitations = (orgId) => {
  return useQuery({
    queryKey: ['organization-invitations', orgId],
    queryFn: async () => {
      const response = await organizationsAPI.invitations(orgId);
      return response.data;
    },
    enabled: !!orgId,
  });
};

export const useCancelInvitation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ orgId, invitationId }) => 
      organizationsAPI.cancelInvitation(orgId, invitationId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['organization-invitations', variables.orgId] });
    },
  });
};

