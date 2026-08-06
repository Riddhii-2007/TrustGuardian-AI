import { apiClient } from './client';
import type { APIResponse, PaginatedResponse } from '../types/common.types';

export interface PsychologyFactors {
  urgency: number;
  authority: number;
  fear: number;
  familiarity: number;
  intent: number;
}

export interface AnalysisResult {
  risk_score: number;
  risk_level: string;
  psychology: PsychologyFactors;
  flags: string[];
  explanation: string;
}

export interface BusinessRequest {
  id: string;
  title: string;
  content: string;
  requester: string;
  created_at: string;
  status: string;
  analysis?: AnalysisResult;
}

export const requestsApi = {
  getRequests: async (): Promise<PaginatedResponse<BusinessRequest>> => {
    const response = await apiClient.get<APIResponse<PaginatedResponse<BusinessRequest>>>('/api/requests/');
    return response.data.data;
  },

  getRequestById: async (id: string): Promise<BusinessRequest> => {
    const response = await apiClient.get<APIResponse<BusinessRequest>>(`/api/requests/${id}`);
    return response.data.data;
  },

  analyzeRequest: async (text: string, subject: string, requester: string): Promise<BusinessRequest> => {
    const response = await apiClient.post<APIResponse<BusinessRequest>>('/api/requests/analyze', {
      text,
      subject,
      requester_email: requester
    });
    return response.data.data;
  }
};
