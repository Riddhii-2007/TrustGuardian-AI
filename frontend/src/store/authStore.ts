import { create } from 'zustand';
import type { AuthState, UserProfile } from '../types/auth.types';
import { supabase } from '../api/supabase';

// ===================================
// TrustGuardian AI — Auth Store
// Zustand store for managing auth state
// ===================================

interface AuthStore extends AuthState {
  setAuth: (user: UserProfile, token: string) => void;
  clearAuth: () => void;
  setLoading: (isLoading: boolean) => void;
  initialize: () => Promise<void>;
  signOut: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isLoading: true, // Start loading to check session on mount

  setAuth: (user, token) => 
    set({ user, accessToken: token, isAuthenticated: true, isLoading: false }),
    
  clearAuth: () => 
    set({ user: null, accessToken: null, isAuthenticated: false, isLoading: false }),
    
  setLoading: (isLoading) => 
    set({ isLoading }),

  initialize: async () => {
    try {
      const { data: { session }, error } = await supabase.auth.getSession();
      
      if (error) {
        console.error('Error fetching session:', error.message);
        set({ user: null, accessToken: null, isAuthenticated: false, isLoading: false });
        return;
      }

      if (session) {
        const userProfile: UserProfile = {
          id: session.user.id,
          email: session.user.email || '',
          full_name: session.user.user_metadata?.full_name || 'Unknown User',
          avatar_url: session.user.user_metadata?.avatar_url,
          role: 'analyst', // Default role for now, would be fetched from DB in prod
          created_at: session.user.created_at,
        };
        
        // Save token for axios interceptor
        localStorage.setItem('supabase-auth-token', session.access_token);
        set({ user: userProfile, accessToken: session.access_token, isAuthenticated: true, isLoading: false });
      } else {
        localStorage.removeItem('supabase-auth-token');
        set({ user: null, accessToken: null, isAuthenticated: false, isLoading: false });
      }

      // Set up auth state listener
      supabase.auth.onAuthStateChange((_event, session) => {
        if (session) {
          const userProfile: UserProfile = {
            id: session.user.id,
            email: session.user.email || '',
            full_name: session.user.user_metadata?.full_name || 'Unknown User',
            avatar_url: session.user.user_metadata?.avatar_url,
            role: 'analyst',
            created_at: session.user.created_at,
          };
          localStorage.setItem('supabase-auth-token', session.access_token);
          set({ user: userProfile, accessToken: session.access_token, isAuthenticated: true, isLoading: false });
        } else {
          localStorage.removeItem('supabase-auth-token');
          set({ user: null, accessToken: null, isAuthenticated: false, isLoading: false });
        }
      });
    } catch (err) {
      console.error('Failed to initialize auth', err);
      set({ user: null, accessToken: null, isAuthenticated: false, isLoading: false });
    }
  },

  signOut: async () => {
    set({ isLoading: true });
    await supabase.auth.signOut();
    localStorage.removeItem('supabase-auth-token');
    set({ user: null, accessToken: null, isAuthenticated: false, isLoading: false });
  }
}));
