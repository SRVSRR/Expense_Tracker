import client from './client';

export interface SuggestResponse {
  suggested_category: string | null;
  confidence: 'high' | 'medium' | 'low' | 'none';
  all_categories: string[];
  source: 'ml' | 'rules' | 'none';
}

export interface CorrectionPayload {
  description: string;
  merchant?: string;
  suggested_category: string;
  corrected_category: string;
}

export interface TrainResponse {
  status: string;
  samples: number;
  accuracy?: number;
  num_classes?: number;
  required?: number;
}

export interface ModelInfo {
  is_trained: boolean;
  training_samples: number;
  model_exists: boolean;
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

  train: async (): Promise<TrainResponse> => {
    const response = await client.post('/api/categorize/train');
    return response.data;
  },

  getModelInfo: async (): Promise<ModelInfo> => {
    const response = await client.get('/api/categorize/model-info');
    return response.data;
  },
};
