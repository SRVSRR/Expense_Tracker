import client from './client';

export interface Account {
  id: string;
  user_id: string;
  name: string;
  currency: string;
  initial_balance: number;
  current_balance?: number;
  created_at: string;
}

export interface CreateAccountPayload {
  name: string;
  currency: string;
  initial_balance: number;
}

export const accountsApi = {
  getAll: async (): Promise<Account[]> => {
    const response = await client.get('/api/accounts');
    return response.data;
  },

  getById: async (id: string): Promise<Account> => {
    const response = await client.get(`/api/accounts/${id}`);
    return response.data;
  },

  create: async (data: CreateAccountPayload): Promise<Account> => {
    const response = await client.post('/api/accounts', data);
    return response.data;
  },

  update: async (id: string, data: Partial<CreateAccountPayload>): Promise<Account> => {
    const response = await client.put(`/api/accounts/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await client.delete(`/api/accounts/${id}`);
  },
};
