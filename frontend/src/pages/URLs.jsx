import { useState } from 'react';
import { Layout } from '../components/Layout';
import { useShortUrls, useCreateShortUrl, useUpdateShortUrl, useDeleteShortUrl, useGenerateQR } from '../hooks/useShortUrls';
import { useNamespaces } from '../hooks/useNamespaces';
import { copyToClipboard } from '../utils/formatters';

export const URLs = () => {
  const { data: urls, isLoading } = useShortUrls();
  const { data: namespaces } = useNamespaces();
  const createUrl = useCreateShortUrl();
  const updateUrl = useUpdateShortUrl();
  const deleteUrl = useDeleteShortUrl();
  const generateQR = useGenerateQR();
  
  const [showModal, setShowModal] = useState(false);
  const [editingUrl, setEditingUrl] = useState(null);
  const [formData, setFormData] = useState({
    namespace_id: '',
    original_url: '',
    short_code: '',
    tags: '',
    is_private: false,
  });
  const [formErrors, setFormErrors] = useState({});

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormErrors({}); // Clear previous errors
    
    try {
      const data = {
        ...formData,
        namespace_id: parseInt(formData.namespace_id),
      };
      if (!data.short_code || !data.short_code.trim()) {
        delete data.short_code; // Let backend generate
      }
      
      if (editingUrl) {
        // Update existing URL
        await updateUrl.mutateAsync({ id: editingUrl.id, data });
      } else {
        // Create new URL
        await createUrl.mutateAsync(data);
      }
      
      setFormData({ namespace_id: '', original_url: '', short_code: '', tags: '', is_private: false });
      setShowModal(false);
      setEditingUrl(null);
    } catch (error) {
      console.error('Form submission error:', error.response?.data || error);
      // Display validation errors from backend
      if (error.response?.data) {
        setFormErrors(error.response.data);
      } else {
        setFormErrors({ general: `Failed to ${editingUrl ? 'update' : 'create'} short URL. Please try again.` });
      }
    }
  };
  
  // Helper function to safely display error messages (handles both string and array formats)
  const getErrorMessage = (error) => {
    if (!error) return null;
    if (Array.isArray(error)) return error[0];
    if (typeof error === 'string') return error;
    return String(error);
  };
  
  const handleEdit = (url) => {
    setEditingUrl(url);
    setFormData({
      namespace_id: url.namespace.id,
      original_url: url.original_url,
      short_code: url.short_code,
      tags: url.tags || '',
      is_private: url.is_private,
    });
    setShowModal(true);
  };
  
  const handleCloseModal = () => {
    setShowModal(false);
    setEditingUrl(null);
    setFormData({ namespace_id: '', original_url: '', short_code: '', tags: '', is_private: false });
    setFormErrors({});
  };

  const handleCopy = async (url) => {
    const success = await copyToClipboard(url);
    if (success) {
      alert('Copied to clipboard!');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this URL?')) {
      await deleteUrl.mutateAsync(id);
    }
  };

  const handleGenerateQR = async (id) => {
    try {
      const result = await generateQR.mutateAsync(id);
      // The result contains the QR code URL
      if (result.data.qr_code) {
        // Open QR code in new tab
        window.open(result.data.qr_code, '_blank');
      } else {
        alert('QR code generated successfully!');
      }
    } catch (error) {
      alert('Failed to generate QR code. Please try again.');
    }
  };

  return (
    <Layout>
      <div className="px-4 py-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Short URLs</h1>
          <button
            onClick={() => setShowModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Create Short URL
          </button>
        </div>

        {isLoading ? (
          <p>Loading...</p>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Short URL</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Original URL</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Clicks</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {urls?.map((url) => (
                  <tr key={url.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <a 
                          href={url.full_short_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-medium text-blue-600 hover:text-blue-800"
                        >
                          {url.full_short_url}
                        </a>
                        <button
                          onClick={() => handleCopy(url.full_short_url)}
                          className="ml-2 text-gray-400 hover:text-gray-600"
                          title="Copy"
                        >
                          📋
                        </button>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <a
                        href={url.original_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-gray-900 hover:underline"
                      >
                        {url.original_url.length > 60 ? 
                        `${url.original_url.substring(0, 60)}...` : url.original_url}
                      </a>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {url.click_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                      <button
                        onClick={() => handleGenerateQR(url.id)}
                        className="text-blue-600 hover:text-blue-800"
                        title="Generate QR Code"
                      >
                        QR
                      </button>
                      <button
                        onClick={() => handleEdit(url)}
                        className="text-green-600 hover:text-green-800"
                        title="Edit"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(url.id)}
                        className="text-red-600 hover:text-red-800"
                        title="Delete"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Create/Edit URL Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
              <h2 className="text-xl font-bold mb-4">
                {editingUrl ? 'Edit Short URL' : 'Create Short URL'}
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* General error message */}
                {(formErrors.general || formErrors.detail || formErrors.non_field_errors) && (
                  <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    <p className="font-semibold">⚠️ Error</p>
                    <p className="mt-1">
                      {formErrors.general || 
                       getErrorMessage(formErrors.detail) || 
                       getErrorMessage(formErrors.non_field_errors)}
                    </p>
                  </div>
                )}
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Namespace *
                  </label>
                  <select
                    value={formData.namespace_id}
                    onChange={(e) => setFormData({ ...formData, namespace_id: e.target.value })}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                      formErrors.namespace_id ? 'border-red-500' : 'border-gray-300'
                    }`}
                    required
                  >
                    <option value="">Select namespace</option>
                    {namespaces?.map((ns) => (
                      <option key={ns.id} value={ns.id}>
                        {ns.name} ({ns.organization.name})
                      </option>
                    ))}
                  </select>
                  {formErrors.namespace_id && (
                    <p className="mt-1 text-sm text-red-600">{getErrorMessage(formErrors.namespace_id)}</p>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Original URL *
                  </label>
                  <input
                    type="url"
                    value={formData.original_url}
                    onChange={(e) => setFormData({ ...formData, original_url: e.target.value })}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                      formErrors.original_url ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="https://example.com"
                    required
                  />
                  {formErrors.original_url && (
                    <p className="mt-1 text-sm text-red-600">{getErrorMessage(formErrors.original_url)}</p>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Custom Short Code (optional)
                  </label>
                  <input
                    type="text"
                    value={formData.short_code}
                    onChange={(e) => {
                      setFormData({ ...formData, short_code: e.target.value });
                      // Clear short_code error when user starts typing
                      if (formErrors.short_code) {
                        setFormErrors({ ...formErrors, short_code: null });
                      }
                    }}
                    className={`w-full px-3 py-2 border-2 rounded-md focus:outline-none focus:ring-2 ${
                      formErrors.short_code 
                        ? 'border-red-500 focus:border-red-500 focus:ring-red-200 bg-red-50' 
                        : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
                    }`}
                    placeholder="my-custom-code"
                  />
                  <p className="mt-1 text-xs text-gray-500">Leave empty to auto-generate</p>
                  {formErrors.short_code && (
                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
                      <p className="text-sm text-red-700 font-semibold flex items-center">
                        <span className="mr-2">❌</span>
                        {getErrorMessage(formErrors.short_code)}
                      </p>
                    </div>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tags (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={formData.tags}
                    onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="marketing, campaign"
                  />
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_private"
                    checked={formData.is_private}
                    onChange={(e) => setFormData({ ...formData, is_private: e.target.checked })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="is_private" className="ml-2 block text-sm text-gray-900">
                    Private URL (requires authentication)
                  </label>
                </div>
                
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={handleCloseModal}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    disabled={editingUrl ? updateUrl.isPending : createUrl.isPending}
                  >
                    {editingUrl 
                      ? (updateUrl.isPending ? 'Updating...' : 'Update')
                      : (createUrl.isPending ? 'Creating...' : 'Create')
                    }
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

