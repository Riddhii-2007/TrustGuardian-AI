import { apiClient } from './client';
import type { APIResponse, PaginatedResponse } from '../types/common.types';

export interface PsychologyFactors {
  urgency: number;
  authority: number;
  fear: number;
  familiarity: number;
  intent: number;
}

export interface QuickResult {
  trust_score: number;
  risk_level: string;
  decision: string;
  summary: string;
}

export interface DetailedReport {
  confidence: number;
  positive_signals: string[];
  negative_signals: string[];
  threats_detected: string[];
  recommendation: string;
  reasoning: string;
  evidence: string[];
  analysis_timestamp: string;
}

export interface AnalysisResult {
  risk_score: number;
  risk_level: string;
  psychology: PsychologyFactors;
  flags: string[];
  explanation: string;
  trust_score: number;
  confidence_score: number;
  verification_required: boolean;
  recommendation: string;
  quick_result?: QuickResult;
  detailed_report?: DetailedReport;
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

export interface OutcomeScenario {
  scenario_id: string;
  description: string;
  probability: number;
  impact_score: number;
}

export interface SimulationResult {
  simulation_id: string;
  request_id: string;
  scenarios: OutcomeScenario[];
  recommendation: string;
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
  },

  simulateOutcome: async (payload: {
    request_id: string;
    action: string;
    parameters: Record<string, any>;
    trust_score?: number;
    confidence_score?: number;
    recommendation?: string;
    flags?: string[];
  }): Promise<SimulationResult> => {
    const response = await apiClient.post<APIResponse<SimulationResult>>('/api/sandbox/simulate', payload);
    return response.data.data;
  }
};
