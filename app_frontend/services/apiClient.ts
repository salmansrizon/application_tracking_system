import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000/api', // Ensure this matches your .env.local or actual backend URL
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add JWT token to requests if available
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('authToken');
      if (token) {
        config.headers['Authorization'] = \`Bearer \${token}\`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default apiClient;
