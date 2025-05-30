'use client'; // This directive is important for Context API with App Router

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiClient from '@/services/apiClient'; // Adjust path as necessary

interface User {
  id: string;
  email: string;
  // Add other user properties you expect from /auth/me
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  login: (token: string) => Promise<void>;
  logout: () => void;
  getToken: () => string | null;
  isLoading: boolean; // To handle initial auth check
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      setToken(storedToken);
      // apiClient.defaults.headers.common['Authorization'] = \`Bearer \${storedToken}\`; // Handled by interceptor
      fetchUser(storedToken);
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchUser = async (currentToken: string) => {
    setIsLoading(true);
    try {
      // apiClient interceptor will add the token.
      // If we just set the token in localStorage and state, the interceptor for this specific call might not pick it up if it runs before the state update is processed.
      // Explicitly setting it here for fetchUser ensures it's present for this critical call.
      const response = await apiClient.get('/auth/me', {
        headers: { 'Authorization': \`Bearer \${currentToken}\` }
      });
      if (response.data) {
        setUser(response.data as User);
        setIsAuthenticated(true);
      } else {
        logout(); // Token might be invalid
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout(); // Token might be invalid or expired
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (newToken: string) => {
    localStorage.setItem('authToken', newToken);
    setToken(newToken);
    // apiClient.defaults.headers.common['Authorization'] = \`Bearer \${newToken}\`; // Handled by interceptor
    await fetchUser(newToken); // Fetch user info after login
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    // delete apiClient.defaults.headers.common['Authorization']; // Interceptor handles absence of token
  };

  const getToken = () => token;

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout, getToken, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
