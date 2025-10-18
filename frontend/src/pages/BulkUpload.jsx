import React, { useState } from 'react';
import { Layout } from '../components/Layout';
import { useBulkUploadTasks, useCreateBulkUpload, useDownloadBulkUpload } from '../hooks/useBulkUpload';
import { useNamespaces } from '../hooks/useNamespaces';
import { useOrganizations } from '../hooks/useOrganizations';

export const BulkUpload = () => {
  const { data: tasks, isLoading } = useBulkUploadTasks();
  const { data: namespaces } = useNamespaces();
  const { data: organizations } = useOrganizations();
  const createUpload = useCreateBulkUpload();
  const downloadResult = useDownloadBulkUpload();
  
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    organization_id: '',
    namespace_id: '',
    file: null,
  });

  const handleFileChange = (e) => {
    setFormData({ ...formData, file: e.target.files[0] });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const data = new FormData();
    data.append('organization_id', formData.organization_id);
    data.append('namespace_id', formData.namespace_id);
    data.append('input_file', formData.file);
    
    await createUpload.mutateAsync(data);
    setFormData({ organization_id: '', namespace_id: '', file: null });
    setShowModal(false);
  };

  const handleDownload = async (taskId) => {
    await downloadResult.mutateAsync(taskId);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'COMPLETED':
        return 'text-green-600 bg-green-100';
      case 'PROCESSING':
        return 'text-blue-600 bg-blue-100';
      case 'FAILED':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <Layout>
      <div className="px-4 py-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Bulk Upload</h1>
          <div className="flex gap-3">
            <a
              href="/api/bulk-upload/template/"
              download
              className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
            >
              Download Template
            </a>
            <button
              onClick={() => setShowModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              Upload Excel File
            </button>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Instructions</h2>
          <div className="text-sm text-gray-600 space-y-2">
            <p>1. Prepare an Excel file with the following columns:</p>
            <ul className="list-disc ml-6 space-y-1">
              <li><strong>original_url</strong> (required): The full URL to shorten</li>
              <li><strong>custom_short_code</strong> (optional): Your desired short code</li>
            </ul>
            <p>2. Select the organization and namespace for these URLs</p>
            <p>3. Upload the file and wait for processing</p>
            <p>4. Download the result file with shortened URLs</p>
          </div>
        </div>

        {isLoading ? (
          <p>Loading...</p>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Namespace</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Progress</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {tasks?.map((task) => (
                  <React.Fragment key={task.id}>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      #{task.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {task.namespace?.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(task.status)}`}>
                        {task.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {task.processed_urls}/{task.total_urls}
                      {task.failed_urls > 0 && ` (${task.failed_urls} failed)`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(task.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {task.status === 'COMPLETED' && task.output_file && (
                        <button
                          onClick={() => handleDownload(task.id)}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          Download Result
                        </button>
                      )}
                      {task.status === 'FAILED' && (
                        <span className="text-red-600 text-xs">
                          Failed
                        </span>
                      )}
                      {task.status === 'PENDING' && (
                        <span className="text-gray-500 text-xs">
                          Waiting...
                        </span>
                      )}
                      {task.status === 'PROCESSING' && (
                        <span className="text-blue-600 text-xs">
                          Processing...
                        </span>
                      )}
                    </td>
                  </tr>
                  {task.status === 'FAILED' && task.error_log && (
                    <tr className="bg-red-50">
                      <td colSpan="6" className="px-6 py-3 text-sm text-red-600">
                        <strong>Error:</strong> {task.error_log}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Upload Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full">
              <h2 className="text-xl font-bold mb-4">Upload Excel File</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Organization *
                  </label>
                  <select
                    value={formData.organization_id}
                    onChange={(e) => setFormData({ ...formData, organization_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  >
                    <option value="">Select organization</option>
                    {organizations?.map((org) => (
                      <option key={org.id} value={org.id}>
                        {org.name}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Namespace *
                  </label>
                  <select
                    value={formData.namespace_id}
                    onChange={(e) => setFormData({ ...formData, namespace_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  >
                    <option value="">Select namespace</option>
                    {namespaces?.map((ns) => (
                      <option key={ns.id} value={ns.id}>
                        {ns.name}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Excel File *
                  </label>
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={handleFileChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                
                <div className="flex justify-end space-x-3 pt-4">
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
                    disabled={createUpload.isPending}
                  >
                    {createUpload.isPending ? 'Uploading...' : 'Upload'}
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

