import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../api/dashboard.api';
import StatsCard from '../components/dashboard/StatsCard';
import RecentActivity from '../components/dashboard/RecentActivity';
import ThreatOverview from '../components/dashboard/ThreatOverview';
import RiskGauge from '../components/dashboard/RiskGauge';
import { AICore } from '../components/dashboard/AICore';
import { TrustScoreGauge } from '../components/dashboard/TrustScoreGauge';
import { supabase } from '../api/supabase';

// ===================================
// TrustGuardian AI — Dashboard Page
// ===================================

const DashboardPage: React.FC = () => {
  const [hasGmailToken] = useState<boolean>(!!localStorage.getItem('google-provider-token'));

  const handleGmailConnect = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          scopes: 'https://www.googleapis.com/auth/gmail.readonly profile email',
          redirectTo: `${window.location.origin}/dashboard`
        }
      });
      if (error) throw error;
    } catch (err) {
      console.error('Failed to connect Gmail:', err);
    }
  };

  // Fetch stats data
  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: dashboardApi.getStats,
  });

  // Fetch recent activity data
  const { data: activity, isLoading: activityLoading, error: activityError } = useQuery({
    queryKey: ['dashboardActivity'],
    queryFn: dashboardApi.getRecentActivity,
  });

  React.useEffect(() => {
    if (activity && activity.length > 0) {
      const latestMail = activity.find(item => item.content);
      if (latestMail && latestMail.content) {
        localStorage.setItem('recent_email_content', latestMail.content);
        
        // Extract sender clean name from description (e.g. From: Kamanaboina Shasheesh <...> | Score: ...)
        const descParts = latestMail.description.split('|');
        const fromPart = descParts[0].replace('From:', '').trim();
        localStorage.setItem('recent_email_sender', fromPart);
        
        // Extract subject from title (e.g. Analyzed: Want money)
        const subPart = latestMail.title.replace('Analyzed:', '').trim();
        localStorage.setItem('recent_email_subject', subPart);
      }
    }
  }, [activity]);

  const isLoading = statsLoading || activityLoading;
  const isError = statsError || activityError;

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-slate-800 border-t-cyan-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (isError || !stats || !activity) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center">
        <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mb-4 border border-red-500/30">
          <span className="text-2xl">⚠️</span>
        </div>
        <h3 className="text-lg font-medium text-slate-200">Failed to load dashboard</h3>
        <p className="text-slate-500 mt-2">Make sure the FastAPI backend is running.</p>
      </div>
    );
  }

  // Dynamically extract trust score from cards if possible
  const trustCard = stats.cards.find(c => c.label.toLowerCase().includes('trust'));
  const isNa = trustCard && trustCard.value === 'N/A';
  const trustScore = trustCard && !isNa ? parseInt(trustCard.value.split('/')[0]) : null;
  const riskLevel = trustScore !== null ? (trustScore > 80 ? 'Low' : trustScore > 50 ? 'Medium' : 'High') : 'N/A';

  return (
    <div className="space-y-8 animate-fade-in pb-8">
      {stats.is_demo_data && (
        <div className="p-4 bg-amber-500/10 border border-amber-500/20 text-amber-300 rounded-xl flex items-center gap-3 shadow-[0_0_20px_rgba(245,158,11,0.05)] backdrop-blur-md">
          <span className="text-xl">⚠️</span>
          <div>
            <h4 className="font-bold text-slate-100 text-sm">Running on Demo Data</h4>
            <p className="text-xs text-slate-400 mt-0.5">Please link your Gmail account using the button on the right to fetch live analysis and dashboard statistics.</p>
          </div>
        </div>
      )}
      <header className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-extrabold text-slate-100 tracking-tight">Enterprise Trust Overview</h2>
          <p className="text-base text-slate-400 mt-2">Real-time analysis of business requests and trust signals.</p>
        </div>
        <div className="flex space-x-3">
          {hasGmailToken ? (
            <button 
              onClick={handleGmailConnect}
              className="px-5 py-2.5 bg-green-500/10 border border-green-500/30 text-green-400 hover:bg-green-500/20 rounded-xl transition-all duration-200 text-sm font-semibold flex items-center gap-2 clickable"
              title="Click to reconnect/refresh token"
            >
              <span className="w-2.5 h-2.5 rounded-full bg-green-500 pulse-dot"></span>
              Gmail Active
            </button>
          ) : (
            <button 
              onClick={handleGmailConnect}
              className="px-5 py-2.5 bg-orange-500/10 border border-orange-500/30 text-orange-400 hover:bg-orange-500/20 rounded-xl transition-all duration-200 text-sm font-semibold flex items-center gap-2 clickable shadow-[0_0_15px_rgba(249,115,22,0.15)] animate-pulse"
            >
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500 pulse-dot"></span>
              Link Gmail
            </button>
          )}
          <button className="px-5 py-2.5 bg-slate-900/60 hover:bg-slate-800/80 text-slate-200 rounded-xl border border-slate-800 transition-all duration-200 text-sm font-semibold clickable">
            Export Report
          </button>
          <Link to="/analyzer" className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl transition-all duration-200 text-sm font-semibold shadow-glow-sm flex items-center justify-center clickable">
            Scan Inbox Now
          </Link>
        </div>
      </header>

      {/* Futuristic Centerpiece Operations Console */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <AICore />
        </div>
        <div className="lg:col-span-1">
          <TrustScoreGauge 
            score={trustScore} 
            confidence={trustScore !== null ? 94 : null} 
            riskLevel={riskLevel} 
          />
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.cards.map((card) => (
          <StatsCard key={card.id} data={card} />
        ))}
      </div>

      {/* Main Grid: Charts & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        {/* Left Column: Charts */}
        <div className="lg:col-span-2 space-y-6 flex flex-col">
          <div className="h-[400px]">
            <RiskGauge data={stats.risk_score_trend} />
          </div>
          <div className="h-[350px]">
            <ThreatOverview threats={stats.threat_overview} />
          </div>
        </div>

        {/* Right Column: Activity Feed */}
        <div className="lg:col-span-1 h-[774px]">
          <RecentActivity activities={activity} />
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
