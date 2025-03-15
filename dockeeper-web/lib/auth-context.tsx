'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import * as auth from './auth';

interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  user: { id: string; email: string } | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<{ id: string; email: string } | null>(null);

  useEffect(() => {
    // Check for saved token on mount
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      setToken(savedToken);
      setIsAuthenticated(true);
      fetchUser(savedToken).catch(() => {
        // If fetching user fails, clear the stored token
        handleLogout();
      });
    }
  }, []);

  const fetchUser = async (accessToken: string) => {
    try {
      const userData = await auth.getCurrentUser(accessToken);
      setUser({ id: userData.id, email: userData.email });
    } catch (error) {
      console.error('Failed to fetch user:', error);
      handleLogout();
      throw error; // Re-throw to handle in the login flow
    }
  };

  const handleLogin = async (email: string, password: string) => {
    try {
      const { access_token, user_id } = await auth.login(email, password);
      
      // First verify we can get the user info with this token
      await fetchUser(access_token);
      
      // If successful, update the state
      setToken(access_token);
      localStorage.setItem('token', access_token);
      setIsAuthenticated(true);
    } catch (error) {
      handleLogout(); // Clear any partial state
      throw error;
    }
  };

  const handleSignup = async (email: string, password: string) => {
    try {
      await auth.signup(email, password);
      // After signup, automatically log in
      await handleLogin(email, password);
    } catch (error) {
      throw error;
    }
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem('token');
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        token,
        user,
        login: handleLogin,
        signup: handleSignup,
        logout: handleLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 