import client from './client';

export interface RecurringRule {
  id: string;
  user_id: string;
  transaction_id?: string;
  pattern: string;
  frequency: number;
  expected_amount: number;
  expected_date: string;
  last_matched?: string;
  created_at: string;
}

export interface UpcomingTransaction {
  id: string;
  rule_id: string;
  pattern: string;
  frequency: number;
  expected_amount: number;
  expected_date: string;
  transaction_id?: string;
}

export interface CreateRecurringRulePayload {
  transaction_id?: string;
  pattern: string;
  frequency: number;
  expected_amount: number;
  expected_date: string;
}

export const recurringApi = {
  getAll: async (): Promise<RecurringRule[]> => {
    const response = await client.get('/api/recurring');
    return response.data;
  },

  getUpcoming: async (days: number = 30): Promise<UpcomingTransaction[]> => {
    const response = await client.get(`/api/recurring/upcoming?days=${days}`);
    return response.data;
  },

  create: async (data: CreateRecurringRulePayload): Promise<RecurringRule> => {
    const response = await client.post('/api/recurring', data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await client.delete(`/api/recurring/${id}`);
  },
};
