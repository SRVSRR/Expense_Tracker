import client from './client';

export interface CashflowForecast {
  current_balance: number;
  daily_projections: Array<{
    date: string;
    projected_income: number;
    projected_expenses: number;
    projected_balance: number;
  }>;
  summary: {
    total_income: number;
    total_expenses: number;
    net_change: number;
  };
}

export interface RunwayData {
  days_until_zero: number;
  current_balance: number;
  avg_daily_burn: number;
  projected_zero_date: string;
}

export interface Anomaly {
  id: string;
  transaction_id: string;
  description: string;
  amount: number;
  category: string;
  expected_range: { min: number; max: number };
  severity: 'low' | 'medium' | 'high';
  detected_at: string;
}

export const forecastApi = {
  getCashflow: async (days?: number): Promise<CashflowForecast> => {
    const params = days ? `?days=${days}` : '';
    const response = await client.get(`/api/forecast/cashflow${params}`);
    return response.data;
  },

  getRunway: async (threshold?: number): Promise<RunwayData> => {
    const params = threshold !== undefined ? `?threshold=${threshold}` : '';
    const response = await client.get(`/api/forecast/runway${params}`);
    return response.data;
  },

  getAnomalies: async (): Promise<Anomaly[]> => {
    const response = await client.get('/api/forecast/anomalies');
    return response.data;
  },
};
