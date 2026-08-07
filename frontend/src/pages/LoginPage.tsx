import React, { useState } from 'react';
import { supabase } from '../api/supabase';
import { CyberGridBackground } from '../components/common/CyberGridBackground';

// ===================================
// TrustGuardian AI — Login Page
// ===================================

const LoginPage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGoogleLogin = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          scopes: 'https://www.googleapis.com/auth/gmail.readonly profile email',
          redirectTo: `${window.location.origin}/dashboard`
        }
      });
      
      if (error) throw error;
      
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.message || 'Failed to authenticate with Google');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#050816] relative overflow-hidden">
      {/* Active interactive cyber canvas grid background */}
      <CyberGridBackground />
      
      {/* Ambient background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/5 rounded-full blur-[120px] pointer-events-none z-0"></div>

      <div className="glass-card w-full max-w-md p-8 relative z-10 shadow-[0_0_50px_rgba(6,182,212,0.15)] border border-slate-800/80">
        <div className="text-center mb-8">
          {/* Futuristic animated HUD shield logo core */}
          <div className="w-24 h-24 relative mx-auto mb-6 flex items-center justify-center">
            {/* Outer dotted scanning ring */}
            <div className="absolute inset-0 border border-dashed border-cyan-500/40 rounded-full animate-[spin_15s_linear_infinite]"></div>
            {/* Inner counter-rotating ring */}
            <div className="absolute inset-2 border border-dotted border-blue-400/30 rounded-full animate-[spin_8s_linear_infinite_reverse]"></div>
            {/* Core glow background */}
            <div className="absolute inset-4 bg-cyan-500/10 rounded-full blur-[6px] animate-pulse"></div>
            {/* Inner active logo core */}
            <svg 
              className="w-10 h-10 text-cyan-400 relative z-10 animate-[bounce_3s_ease-in-out_infinite]" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="1.5"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.249-8.25-3.286zm0 3.036v13.5" />
            </svg>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-100 gradient-text mb-2">TrustGuardian AI</h1>
          <p className="text-slate-400 text-sm font-semibold tracking-wide">Enterprise Trust Intelligence Platform</p>
        </div>

        <div className="space-y-4">
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm text-center">
              {error}
            </div>
          )}
          
          <button 
            onClick={handleGoogleLogin}
            disabled={isLoading}
            className="w-full flex items-center justify-center space-x-3 bg-slate-800 hover:bg-slate-700 text-white p-3 rounded-lg border border-slate-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-slate-400 border-t-white rounded-full animate-spin"></div>
            ) : (
              <svg className="w-5 h-5 group-hover:scale-110 transition-transform" viewBox="0 0 24 24">
                <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
            )}
            <span className="font-medium">{isLoading ? 'Connecting...' : 'Continue with Google'}</span>
          </button>

          <div className="mt-6 text-center">
             <p className="text-xs text-slate-500 max-w-xs mx-auto">
               Requires Google Workspace access to analyze business requests and trust signals.
             </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
