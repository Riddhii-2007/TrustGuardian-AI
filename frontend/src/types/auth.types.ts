// ===================================
// Auth Type Definitions
// ===================================

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  role: 'admin' | 'analyst' | 'viewer';
  organization?: string;
  created_at: string;
}

export interface AuthState {
  user: UserProfile | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
