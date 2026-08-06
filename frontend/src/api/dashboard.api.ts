import { apiClient } from './client';
import type { APIResponse } from '../types/common.types';

// ===================================
// TrustGuardian AI — Dashboard API
// ===================================

export interface StatCardData {
  id: string;
  label: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  color: string;
}

export interface ThreatCategory {
  name: string;
  count: number;
  color: string;
}

export interface DashboardStats {
  cards: StatCardData[];
  threat_overview: ThreatCategory[];
  risk_score_trend: { date: string; score: number }[];
}

export interface ActivityItem {
  id: string;
  type: 'alert' | 'analysis' | 'workflow';
  title: string;
  description: string;
  timestamp: string;
  risk_level: 'critical' | 'high' | 'medium' | 'low' | 'safe';
}

export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    const response = await apiClient.get<APIResponse<DashboardStats>>('/api/dashboard/stats');
    return response.data.data;
  },

  getRecentActivity: async (): Promise<ActivityItem[]> => {
    const response = await apiClient.get<APIResponse<ActivityItem[]>>('/api/dashboard/recent-activity');
    return response.data.data;
  }
};
