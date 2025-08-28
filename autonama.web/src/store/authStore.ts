import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserResponse } from '@/types/user';

interface AuthState {
  user: UserResponse | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthActions {
  loginStart: () => void;
  loginSuccess: (user: UserResponse, token: string) => void;
  loginFailure: (error: string) => void;
  logout: () => void;
  clearError: () => void;
  setUser: (user: UserResponse | null) => void;
}

type AuthStore = AuthState & AuthActions;

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      loginStart: () => set({ isLoading: true, error: null }),
      
      loginSuccess: (user: UserResponse, token: string) => set({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      }),
      
      loginFailure: (error: string) => set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error,
      }),
      
      logout: () => set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      }),
      
      clearError: () => set({ error: null }),
      
      setUser: (user: UserResponse | null) => set({
        user,
        isAuthenticated: !!user,
      }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        token: state.token, 
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
);

