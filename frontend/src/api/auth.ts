import client from './client';

export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
}

export const authApi = {
  register: async (email: string, password: string): Promise<User> => {
    const response = await client.post('/api/auth/register', { email, password });
    return response.data;
  },

  login: async (email: string, password: string): Promise<LoginResponse> => {
    const response = await client.post('/api/auth/login', { email, password });
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await client.get('/api/auth/me');
    return response.data;
  },
};
