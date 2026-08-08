import { createClient } from '@supabase/supabase-js';

// ===================================
// TrustGuardian AI — Supabase Client
// ===================================

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

export const isSupabaseConfigured = !!(supabaseUrl && supabaseAnonKey);

let supabaseClient: any;

if (isSupabaseConfigured) {
  try {
    supabaseClient = createClient(supabaseUrl, supabaseAnonKey);
  } catch (err) {
    console.error('Failed to initialize Supabase client:', err);
    supabaseClient = createMockClient();
  }
} else {
  console.warn("Supabase VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY is missing! Using mock offline mode.");
  supabaseClient = createMockClient();
}

function createMockClient() {
  return {
    auth: {
      getSession: async () => ({ data: { session: null }, error: null }),
      onAuthStateChange: (callback: any) => {
        // Trigger empty initial session callback
        setTimeout(() => callback('SIGNED_OUT', null), 0);
        return { data: { subscription: { unsubscribe: () => {} } } };
      },
      signInWithOAuth: async () => ({ 
        error: new Error("Supabase is not configured. Please create a 'frontend/.env' file with valid VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.") 
      }),
      signOut: async () => {},
    }
  };
}

export const supabase = supabaseClient;
