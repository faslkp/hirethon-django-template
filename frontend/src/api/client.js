import axios from 'axios';

// Use relative URLs to leverage Vite proxy in development
// In production, set VITE_API_URL environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for cookies/CSRF tokens
});

// Add request interceptor to include JWT token and CSRF token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add CSRF token for non-API endpoints (like session-based login)
    if (config.url && !config.url.startsWith('/api/') && !config.url.startsWith('/rest-auth/')) {
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Track if we're currently refreshing to avoid multiple simultaneous refresh attempts
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  failedQueue = [];
};

// Add response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and haven't retried yet, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      
      // If already refreshing, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch(err => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');
      
      if (!refreshToken) {
        console.warn('No refresh token available, redirecting to login...');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        console.log('Access token expired, attempting to refresh...');
        const response = await axios.post('/rest-auth/token/refresh/', {
          refresh: refreshToken,
        }, { withCredentials: true });

        const { access, access_token } = response.data;
        const newAccessToken = access || access_token;
        
        if (!newAccessToken) {
          throw new Error('No access token in refresh response');
        }

        console.log('Token refreshed successfully');
        localStorage.setItem('access_token', newAccessToken);
        
        // Update the authorization header
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`;
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        
        processQueue(null, newAccessToken);
        isRefreshing = false;
        
        return apiClient(originalRequest);
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError.response?.data || refreshError.message);
        processQueue(refreshError, null);
        isRefreshing = false;
        
        // Refresh failed, clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Only redirect if not already on login page
        if (window.location.pathname !== '/login') {
          console.warn('Redirecting to login page...');
          window.location.href = '/login';
        }
        
        return Promise.reject(refreshError);
      }
    }

    // Log other errors for debugging
    if (error.response) {
      console.error('API Error:', {
        status: error.response.status,
        url: error.config?.url,
        data: error.response.data,
      });
    }

    return Promise.reject(error);
  }
);

export default apiClient;

