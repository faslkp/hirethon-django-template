import axios from 'axios';

// Use relative URLs to leverage Vite proxy in development
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const authAPI = {
  login: async (email, password) => {
    const response = await axios.post(`${API_BASE_URL}/rest-auth/login/`, {
      email,
      password,
    }, { withCredentials: true });
    return response.data;
  },

  register: async (email, password1, password2, name) => {
    const response = await axios.post(`${API_BASE_URL}/rest-auth/registration/`, {
      email,
      password1,
      password2,
      name,
    }, { withCredentials: true });
    return response.data;
  },

  logout: async () => {
    const token = localStorage.getItem('access_token');
    const response = await axios.post(
      `${API_BASE_URL}/rest-auth/logout/`,
      {},
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        withCredentials: true,
      }
    );
    return response.data;
  },

  getCurrentUser: async (token) => {
    const response = await axios.get(`${API_BASE_URL}/rest-auth/user/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      withCredentials: true,
    });
    return response.data;
  },

  refreshToken: async (refreshToken) => {
    const response = await axios.post(`${API_BASE_URL}/rest-auth/token/refresh/`, {
      refresh: refreshToken,
    }, { withCredentials: true });
    return response.data;
  },

  googleLogin: async (accessToken) => {
    const response = await axios.post(`${API_BASE_URL}/api/auth/google/`, {
      access_token: accessToken,
    });
    return response.data;
  },
};

