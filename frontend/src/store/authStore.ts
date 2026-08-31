import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { authApi, User } from '../api/auth';

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loadToken: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    await SecureStore.setItemAsync('auth_token', response.access_token);
    const user = await authApi.getMe();
    set({ token: response.access_token, user, isAuthenticated: true });
  },

  register: async (email: string, password: string) => {
    await authApi.register(email, password);
    const response = await authApi.login(email, password);
    await SecureStore.setItemAsync('auth_token', response.access_token);
    const user = await authApi.getMe();
    set({ token: response.access_token, user, isAuthenticated: true });
  },

  logout: async () => {
    await SecureStore.deleteItemAsync('auth_token');
    set({ token: null, user: null, isAuthenticated: false });
  },

  loadToken: async () => {
    try {
      const token = await SecureStore.getItemAsync('auth_token');
      if (token) {
        set({ token, isLoading: false });
        const user = await authApi.getMe();
        set({ user, isAuthenticated: true, isLoading: false });
      } else {
        set({ isLoading: false });
      }
    } catch {
      await SecureStore.deleteItemAsync('auth_token');
      set({ isLoading: false });
    }
  },
}));
