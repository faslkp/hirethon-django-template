import { create } from 'zustand';
import { authAPI } from '../api/auth';

export const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (email, password) => {
    try {
      const data = await authAPI.login(email, password);
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      
      // Get user info
      const user = await authAPI.getCurrentUser(data.access);
      set({ user, isAuthenticated: true });
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data || 'Login failed' 
      };
    }
  },

  register: async (email, password1, password2, name) => {
    try {
      const data = await authAPI.register(email, password1, password2, name);
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      
      // Get user info
      const user = await authAPI.getCurrentUser(data.access);
      set({ user, isAuthenticated: true });
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data || 'Registration failed' 
      };
    }
  },

  logout: async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ user: null, isAuthenticated: false });
    }
  },

  checkAuth: async () => {
    const token = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (!token) {
      set({ isLoading: false, isAuthenticated: false });
      return;
    }

    try {
      const user = await authAPI.getCurrentUser(token);
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      console.warn('checkAuth failed:', error.response?.status);
      
      // If 401 and we have a refresh token, try to refresh
      if (error.response?.status === 401 && refreshToken) {
        try {
          console.log('Attempting token refresh during auth check...');
          const data = await authAPI.refreshToken(refreshToken);
          const newAccessToken = data.access || data.access_token;
          
          if (newAccessToken) {
            localStorage.setItem('access_token', newAccessToken);
            const user = await authAPI.getCurrentUser(newAccessToken);
            set({ user, isAuthenticated: true, isLoading: false });
            return;
          }
        } catch (refreshError) {
          console.error('Token refresh during auth check failed:', refreshError);
        }
      }
      
      // If all else fails, clear auth
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  // Method to manually refresh token
  refreshToken: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      return { success: false, error: 'No refresh token' };
    }

    try {
      const data = await authAPI.refreshToken(refreshToken);
      const newAccessToken = data.access || data.access_token;
      
      if (newAccessToken) {
        localStorage.setItem('access_token', newAccessToken);
        return { success: true };
      }
      return { success: false, error: 'No access token in response' };
    } catch (error) {
      console.error('Manual token refresh failed:', error);
      return { success: false, error: error.response?.data || 'Refresh failed' };
    }
  },

  googleLogin: async (accessToken) => {
    try {
      const data = await authAPI.googleLogin(accessToken);
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      
      // Get user info
      const user = await authAPI.getCurrentUser(data.access);
      set({ user, isAuthenticated: true });
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data || 'Google login failed' 
      };
    }
  },
}));

