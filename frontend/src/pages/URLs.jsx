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
    expires_at: '',
  });
  const [formErrors, setFormErrors] = useState({});
  
  // Tag filtering state
  const [selectedTags, setSelectedTags] = useState([]);
  const [tagSortBy, setTagSortBy] = useState('recent'); // 'recent' or 'popular'

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
      if (!data.expires_at || !data.expires_at.trim()) {
        delete data.expires_at; // Remove empty expiry date
      }
      
      if (editingUrl) {
        // Update existing URL
        await updateUrl.mutateAsync({ id: editingUrl.id, data });
      } else {
        // Create new URL
        await createUrl.mutateAsync(data);
      }
      
      setFormData({ namespace_id: '', original_url: '', short_code: '', tags: '', is_private: false, expires_at: '' });
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
      expires_at: url.expires_at ? url.expires_at.split('T')[0] : '', // Convert to date input format
    });
    setShowModal(true);
  };
  
  const handleCloseModal = () => {
    setShowModal(false);
    setEditingUrl(null);
    setFormData({ namespace_id: '', original_url: '', short_code: '', tags: '', is_private: false, expires_at: '' });
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

  // Tag filtering functions
  const toggleTagFilter = (tag) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const clearAllTagFilters = () => {
    setSelectedTags([]);
  };

  const getAllTags = () => {
    if (!urls) return [];
    const allTags = urls.flatMap(url => 
      url.tags ? url.tags.split(',').map(tag => tag.trim()).filter(tag => tag) : []
    );
    return [...new Set(allTags)]; // Remove duplicates
  };

  const getSortedTags = () => {
    const tags = getAllTags();
    if (tagSortBy === 'popular') {
      // Sort by frequency
      const tagCounts = {};
      urls.forEach(url => {
        if (url.tags) {
          url.tags.split(',').forEach(tag => {
            const trimmedTag = tag.trim();
            if (trimmedTag) {
              tagCounts[trimmedTag] = (tagCounts[trimmedTag] || 0) + 1;
            }
          });
        }
      });
      return tags.sort((a, b) => (tagCounts[b] || 0) - (tagCounts[a] || 0));
    } else {
      // Sort by recent (alphabetical for now)
      return tags.sort();
    }
  };

  const getFilteredUrls = () => {
    if (!urls) return [];
    if (selectedTags.length === 0) return urls;
    
    return urls.filter(url => {
      if (!url.tags) return false;
      const urlTags = url.tags.split(',').map(tag => tag.trim());
      return selectedTags.some(selectedTag => urlTags.includes(selectedTag));
    });
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

        {/* Tag Filtering Section */}
        {!isLoading && urls && urls.length > 0 && (
          <div className="bg-white shadow rounded-lg p-4 mb-6">
            <div className="flex items-center space-x-4">
              <h3 className="text-sm font-medium text-gray-900 whitespace-nowrap">Filter by tags</h3>
              <select
                  value={tagSortBy}
                  onChange={(e) => setTagSortBy(e.target.value)}
                  className="px-2 py-1 border border-gray-300 rounded text-xs"
                >
                  <option value="recent">Recent first</option>
                  <option value="popular">Popular first</option>
                </select>

              <div className="flex items-center space-x-2 flex-1 overflow-x-auto scrollbar-thin">
                {getSortedTags().map((tag) => (
                  <button
                    key={tag}
                    onClick={() => toggleTagFilter(tag)}
                    className={`px-3 py-1 rounded-full text-sm whitespace-nowrap transition-colors ${
                      selectedTags.includes(tag)
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
              
              <div className="flex items-center space-x-2 whitespace-nowrap">
                {selectedTags.length > 0 && (
                  <button
                    onClick={clearAllTagFilters}
                    className="text-xs text-gray-500 hover:text-gray-700"
                  >
                    Clear all
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {isLoading ? (
          <p>Loading...</p>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200" style={{ minWidth: '1200px' }}>
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Short URL</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Original URL</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created By</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created At</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Expiry</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Clicks</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase sticky right-0 bg-gray-50 border-l border-gray-200">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {getFilteredUrls()?.map((url) => (
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
                        title={url.original_url}
                      >
                        {url.original_url.length > 30 ? 
                        `${url.original_url.substring(0, 30)}...` : url.original_url}
                      </a>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {url.created_by?.name || url.created_by?.email || 'Unknown'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(url.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {url.expires_at ? (
                        <span className={new Date(url.expires_at) < new Date() ? 'text-red-600' : 'text-gray-500'}>
                          {new Date(url.expires_at).toLocaleDateString()}
                        </span>
                      ) : (
                        <span className="text-gray-500">Never</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {url.click_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm sticky right-0 bg-white border-l border-gray-200">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleGenerateQR(url.id)}
                          className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
                          title="Generate QR Code"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleEdit(url)}
                          className="p-1 text-green-600 hover:text-green-800 hover:bg-green-50 rounded"
                          title="Edit"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDelete(url.id)}
                          className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                          title="Delete"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
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
                
                <div>
                  <label htmlFor="expires_at" className="block text-sm font-medium text-gray-700 mb-1">
                    Expiry Date (optional)
                  </label>
                  <input
                    type="date"
                    id="expires_at"
                    value={formData.expires_at}
                    onChange={(e) => setFormData({ ...formData, expires_at: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">Leave empty for no expiration</p>
                  {formErrors.expires_at && (
                    <p className="mt-1 text-sm text-red-600">{getErrorMessage(formErrors.expires_at)}</p>
                  )}
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

