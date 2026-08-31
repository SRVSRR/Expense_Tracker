import client from './client';

export interface Category {
  id: string;
  user_id?: string;
  name: string;
  type: 'income' | 'expense';
  parent_id?: string;
  color?: string;
  icon?: string;
}

export interface CreateCategoryPayload {
  name: string;
  type: 'income' | 'expense';
  parent_id?: string;
  color?: string;
  icon?: string;
}

export const categoriesApi = {
  getAll: async (): Promise<Category[]> => {
    const response = await client.get('/api/categories');
    return response.data;
  },

  create: async (data: CreateCategoryPayload): Promise<Category> => {
    const response = await client.post('/api/categories', data);
    return response.data;
  },
};
