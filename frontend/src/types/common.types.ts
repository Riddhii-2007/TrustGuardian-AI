// ===================================
// TrustGuardian AI — Type Definitions
// Common types used across the app
// ===================================

export interface APIResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ErrorResponse {
  success: false;
  error: string;
  detail?: string;
  status_code: number;
}

export type RiskLevel = 'critical' | 'high' | 'medium' | 'low' | 'safe';

export interface RiskScore {
  value: number;       // 0-100
  level: RiskLevel;
  label: string;
}
