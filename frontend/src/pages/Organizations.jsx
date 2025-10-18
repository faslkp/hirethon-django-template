import { useState } from 'react';
import { Layout } from '../components/Layout';
import { useOrganizations, useCreateOrganization } from '../hooks/useOrganizations';
import { Link } from 'react-router-dom';

export const Organizations = () => {
  const { data: organizations, isLoading } = useOrganizations();
  const createOrg = useCreateOrganization();
  const [showModal, setShowModal] = useState(false);
  const [orgName, setOrgName] = useState('');

  const handleCreate = async (e) => {
    e.preventDefault();
    await createOrg.mutateAsync({ name: orgName });
    setOrgName('');
    setShowModal(false);
  };

  return (
    <Layout>
      <div className="px-4 py-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Organizations</h1>
          <button
            onClick={() => setShowModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Create Organization
          </button>
        </div>

        {isLoading ? (
          <p>Loading...</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {organizations?.map((org) => (
              <Link
                key={org.id}
                to={`/organizations/${org.id}`}
                className="block bg-white rounded-lg shadow hover:shadow-lg transition p-6"
              >
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{org.name}</h3>
                <div className="text-sm text-gray-600 space-y-1">
                  <p>Role: <span className="font-medium text-blue-600">{org.user_role}</span></p>
                  <p>Members: {org.member_count}</p>
                  <p>Namespaces: {org.namespace_count}</p>
                  <p>Created: {new Date(org.created_at).toLocaleDateString()}</p>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* Create Organization Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full">
              <h2 className="text-xl font-bold mb-4">Create Organization</h2>
              <form onSubmit={handleCreate}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Organization Name
                  </label>
                  <input
                    type="text"
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    disabled={createOrg.isPending}
                  >
                    {createOrg.isPending ? 'Creating...' : 'Create'}
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

