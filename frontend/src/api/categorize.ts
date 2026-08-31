import client from './client';

export interface SuggestResponse {
  suggested_category: string | null;
  confidence: 'high' | 'medium' | 'low' | 'none';
  all_categories: string[];
}

export interface CorrectionPayload {
  description: string;
  merchant?: string;
  suggested_category: string;
  corrected_category: string;
}

export const categorizeApi = {
  suggest: async (description: string, merchant?: string): Promise<SuggestResponse> => {
    const response = await client.post('/api/categorize/suggest', {
      description,
      merchant,
    });
    return response.data;
  },

  logCorrection: async (data: CorrectionPayload): Promise<void> => {
    await client.post('/api/categorize/corrections', data);
  },
};
