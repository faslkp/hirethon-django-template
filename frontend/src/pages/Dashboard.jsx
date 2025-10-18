import { Layout } from '../components/Layout';
import { useOrganizations } from '../hooks/useOrganizations';
import { useShortUrls } from '../hooks/useShortUrls';
import { Link } from 'react-router-dom';

export const Dashboard = () => {
  const { data: organizations, isLoading: orgsLoading } = useOrganizations();
  const { data: urls, isLoading: urlsLoading } = useShortUrls();

  return (
    <Layout>
      <div className="px-4 py-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Organizations</h3>
            <p className="text-3xl font-bold text-blue-600">
              {orgsLoading ? '...' : organizations?.length || 0}
            </p>
            <Link to="/organizations" className="text-sm text-blue-600 hover:underline mt-2 inline-block">
              View all →
            </Link>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Short URLs</h3>
            <p className="text-3xl font-bold text-green-600">
              {urlsLoading ? '...' : urls?.length || 0}
            </p>
            <Link to="/urls" className="text-sm text-blue-600 hover:underline mt-2 inline-block">
              View all →
            </Link>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Clicks</h3>
            <p className="text-3xl font-bold text-purple-600">
              {urlsLoading ? '...' : urls?.reduce((sum, url) => sum + (url.click_count || 0), 0) || 0}
            </p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Recent URLs</h2>
          {urlsLoading ? (
            <p>Loading...</p>
          ) : urls && urls.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Short Code
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Original URL
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Clicks
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {urls.slice(0, 5).map((url) => (
                    <tr key={url.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <a 
                          href={url.full_short_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800"
                        >
                          {url.full_short_url}
                        </a>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {url.original_url.length > 50
                          ? `${url.original_url.substring(0, 50)}...`
                          : url.original_url}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {url.click_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(url.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500">No URLs created yet.</p>
          )}
        </div>
      </div>
    </Layout>
  );
};

