import axios, { type InternalAxiosRequestConfig } from 'axios';

// ===================================
// TrustGuardian AI — API Client
// ===================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // 10 second timeout for AI operations
  timeout: 10000,
});

// Request Interceptor: Attach auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // We will hook this up to Supabase auth state later
    const token = localStorage.getItem('supabase-auth-token');
    const providerToken = localStorage.getItem('google-provider-token');
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    if (providerToken && config.headers) {
      config.headers['X-Google-Provider-Token'] = providerToken;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle errors globally
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle 401 Unauthorized
    if (error.response?.status === 401) {
      // Clear token and redirect to login (handled in auth store)
      console.error('Authentication expired');
    }
    
    return Promise.reject(error);
  }
);
