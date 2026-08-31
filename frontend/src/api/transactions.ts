import client from './client';

export interface Transaction {
  id: string;
  user_id: string;
  account_id: string;
  type: 'income' | 'expense';
  amount: number;
  category: string;
  description: string;
  merchant?: string;
  date: string;
  is_recurring: number;
  created_at: string;
}

export interface CreateTransactionPayload {
  account_id: string;
  type: 'income' | 'expense';
  amount: number;
  category: string;
  description: string;
  merchant?: string;
  date: string;
  is_recurring?: number;
}

export interface TransactionFilters {
  account_id?: string;
  type?: string;
  category?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

export const transactionsApi = {
  getAll: async (filters?: TransactionFilters): Promise<Transaction[]> => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
          params.append(key, String(value));
        }
      });
    }
    const response = await client.get(`/api/transactions?${params.toString()}`);
    return response.data;
  },

  getById: async (id: string): Promise<Transaction> => {
    const response = await client.get(`/api/transactions/${id}`);
    return response.data;
  },

  create: async (data: CreateTransactionPayload): Promise<Transaction> => {
    const response = await client.post('/api/transactions', data);
    return response.data;
  },

  update: async (id: string, data: Partial<CreateTransactionPayload>): Promise<Transaction> => {
    const response = await client.put(`/api/transactions/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await client.delete(`/api/transactions/${id}`);
  },
};
