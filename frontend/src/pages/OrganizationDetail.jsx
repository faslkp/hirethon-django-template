import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { 
  useOrganization, 
  useOrganizationMembers, 
  useInviteMember,
  useOrganizationInvitations,
  useCancelInvitation 
} from '../hooks/useOrganizations';
import { useCreateNamespace } from '../hooks/useNamespaces';

export const OrganizationDetail = () => {
  const { id } = useParams();
  const { data: organization, isLoading, refetch: refetchOrganization } = useOrganization(id);
  const { data: members, isLoading: membersLoading, error: membersError } = useOrganizationMembers(id);
  const { data: invitations } = useOrganizationInvitations(id);
  
  // Use members from organization data if available, otherwise use separate API call
  const displayMembers = organization?.memberships || members;
  const inviteMember = useInviteMember();
  const cancelInvitation = useCancelInvitation();
  const createNamespace = useCreateNamespace();
  
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showNamespaceModal, setShowNamespaceModal] = useState(false);
  const [inviteData, setInviteData] = useState({ email: '', role: 'VIEWER' });
  const [namespaceName, setNamespaceName] = useState('');
  const [inviteSuccess, setInviteSuccess] = useState(null);
  const [inviteError, setInviteError] = useState(null);

  const handleInvite = async (e) => {
    e.preventDefault();
    setInviteError(null); // Clear any previous errors
    
    try {
      const result = await inviteMember.mutateAsync({
        orgId: id,
        data: inviteData,
      });
      
      // Check if it's an invitation or direct membership
      if (result.data.message) {
        // Unregistered user - invitation sent
        setInviteSuccess({
          type: 'invitation',
          email: inviteData.email,
          message: 'Invitation email sent successfully!'
        });
      } else {
        // Registered user - added directly
        setInviteSuccess({
          type: 'membership',
          email: inviteData.email,
          message: 'Member added successfully!'
        });
      }
      
      setInviteData({ email: '', role: 'VIEWER' });
      
      // Close modal after 2 seconds
      setTimeout(() => {
        setShowInviteModal(false);
        setInviteSuccess(null);
      }, 2000);
    } catch (error) {
      console.error('Invite error:', error);
      
      // Extract error message from the response
      let errorMessage = 'Failed to send invitation. Please try again.';
      
      if (error.response?.data) {
        const errorData = error.response.data;
        
        // Handle field-specific errors
        if (errorData.email && Array.isArray(errorData.email)) {
          errorMessage = errorData.email[0];
        } else if (errorData.non_field_errors && Array.isArray(errorData.non_field_errors)) {
          errorMessage = errorData.non_field_errors[0];
        } else if (typeof errorData === 'string') {
          errorMessage = errorData;
        }
      }
      
      setInviteError(errorMessage);
    }
  };

  const handleCancelInvitation = async (invitationId) => {
    if (window.confirm('Are you sure you want to cancel this invitation?')) {
      await cancelInvitation.mutateAsync({ orgId: id, invitationId });
    }
  };

  const handleCreateNamespace = async (e) => {
    e.preventDefault();
    try {
      await createNamespace.mutateAsync({
        name: namespaceName,
        organization_id: parseInt(id),
      });
      setNamespaceName('');
      setShowNamespaceModal(false);
      // Force a refetch of the organization data
      await refetchOrganization();
    } catch (error) {
      console.error('Failed to create namespace:', error);
    }
  };

  if (isLoading) return <Layout><p>Loading...</p></Layout>;

  const isAdmin = organization?.user_role === 'ADMIN';

  return (
    <Layout>
      <div className="px-4 py-6">
        <div className="mb-6">
          <Link to="/organizations" className="text-blue-600 hover:underline mb-2 inline-block">
            ← Back to Organizations
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">{organization?.name}</h1>
          <p className="text-gray-600 mt-1">Your role: <span className="font-medium">{organization?.user_role}</span></p>
        </div>

        {/* Namespaces Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Namespaces</h2>
            {isAdmin && (
              <button
                onClick={() => setShowNamespaceModal(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm"
              >
                Create Namespace
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {organization?.namespaces?.map((namespace) => (
              <div key={namespace.id} className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg">{namespace.name}</h3>
                <p className="text-sm text-gray-600 mt-1">{namespace.url_count} URLs</p>
              </div>
            )) || <p className="text-gray-500">No namespaces yet</p>}
          </div>
        </div>

        {/* Members Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Members</h2>
            {isAdmin && (
              <button
                onClick={() => {
                  setShowInviteModal(true);
                  setInviteError(null);
                  setInviteSuccess(null);
                }}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm"
              >
                Invite Member
              </button>
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Joined</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {(isLoading || membersLoading) ? (
                  <tr>
                    <td colSpan="3" className="px-6 py-4 text-center text-sm text-gray-500">
                      Loading members...
                    </td>
                  </tr>
                ) : membersError ? (
                  <tr>
                    <td colSpan="3" className="px-6 py-4 text-center text-sm text-red-500">
                      Error loading members: {membersError.message}
                    </td>
                  </tr>
                ) : displayMembers && displayMembers.length > 0 ? (
                  displayMembers.map((member) => (
                    <tr key={member.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {member.user?.email || 'No email'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-600">
                          {member.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {member.joined_at ? new Date(member.joined_at).toLocaleDateString() : 'Unknown'}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="3" className="px-6 py-4 text-center text-sm text-gray-500">
                      No members found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pending Invitations Section */}
        {isAdmin && invitations && invitations.length > 0 && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Pending Invitations</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invited</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Expires</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {invitations.map((invitation) => (
                    <tr key={invitation.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {invitation.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-600">
                          {invitation.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(invitation.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(invitation.expires_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => handleCancelInvitation(invitation.id)}
                          className="text-red-600 hover:text-red-800"
                          disabled={cancelInvitation.isPending}
                        >
                          Cancel
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Invite Member Modal */}
        {showInviteModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full">
              <h2 className="text-xl font-bold mb-4">Invite Member</h2>
              
              {inviteSuccess ? (
                <div className="py-8 text-center">
                  <div className="mb-4 text-green-600 text-5xl">✓</div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {inviteSuccess.message}
                  </h3>
                  <p className="text-gray-600">
                    {inviteSuccess.type === 'invitation' 
                      ? `An invitation email has been sent to ${inviteSuccess.email}`
                      : `${inviteSuccess.email} has been added to the organization`
                    }
                  </p>
                </div>
              ) : (
                <form onSubmit={handleInvite} className="space-y-4">
                  {inviteError && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
                      {inviteError}
                    </div>
                  )}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Email *</label>
                    <input
                      type="email"
                      value={inviteData.email}
                      onChange={(e) => {
                        setInviteData({ ...inviteData, email: e.target.value });
                        setInviteError(null); // Clear error when user types
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      required
                      disabled={inviteMember.isPending}
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      We'll send an invitation if the user doesn't have an account yet
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Role *</label>
                    <select
                      value={inviteData.role}
                      onChange={(e) => setInviteData({ ...inviteData, role: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      required
                      disabled={inviteMember.isPending}
                    >
                      <option value="VIEWER">Viewer</option>
                      <option value="EDITOR">Editor</option>
                      <option value="ADMIN">Admin</option>
                    </select>
                  </div>
                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={() => {
                        setShowInviteModal(false);
                        setInviteSuccess(null);
                        setInviteError(null);
                      }}
                      className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                      disabled={inviteMember.isPending}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                      disabled={inviteMember.isPending}
                    >
                      {inviteMember.isPending ? 'Sending...' : 'Send Invite'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}

        {/* Create Namespace Modal */}
        {showNamespaceModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full">
              <h2 className="text-xl font-bold mb-4">Create Namespace</h2>
              <form onSubmit={handleCreateNamespace} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Namespace Name *
                  </label>
                  <input
                    type="text"
                    value={namespaceName}
                    onChange={(e) => setNamespaceName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="my-namespace"
                    pattern="[a-z0-9-]+"
                    title="Only lowercase letters, numbers, and hyphens"
                    required
                  />
                  <p className="mt-1 text-xs text-gray-500">Globally unique, lowercase letters, numbers, and hyphens only</p>
                </div>
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowNamespaceModal(false)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    disabled={createNamespace.isPending}
                  >
                    {createNamespace.isPending ? 'Creating...' : 'Create'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

