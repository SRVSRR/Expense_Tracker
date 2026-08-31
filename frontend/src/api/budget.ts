import client from './client';

export interface BudgetRecommendation {
  category: string;
  recommended_limit: number;
  historical_average: number;
  trend: 'increasing' | 'decreasing' | 'stable';
  confidence: number;
}

export interface CategoryAnalysis {
  category: string;
  total_spent: number;
  transaction_count: number;
  average_per_transaction: number;
  percentage_of_total: number;
  month_over_month_change: number;
}

export const budgetApi = {
  getRecommendations: async (): Promise<BudgetRecommendation[]> => {
    const response = await client.get('/api/budget/recommendations');
    return response.data;
  },

  getCategoryAnalysis: async (): Promise<CategoryAnalysis[]> => {
    const response = await client.get('/api/budget/category-analysis');
    return response.data;
  },
};
