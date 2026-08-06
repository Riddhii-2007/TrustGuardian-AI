import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../api/dashboard.api';
import StatsCard from '../components/dashboard/StatsCard';
import RecentActivity from '../components/dashboard/RecentActivity';
import ThreatOverview from '../components/dashboard/ThreatOverview';
import RiskGauge from '../components/dashboard/RiskGauge';

// ===================================
// TrustGuardian AI — Dashboard Page
// ===================================

const DashboardPage: React.FC = () => {
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

  const isLoading = statsLoading || activityLoading;
  const isError = statsError || activityError;

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-slate-700 border-t-cyan-500 rounded-full animate-spin"></div>
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

  return (
    <div className="space-y-6 animate-fade-in pb-8">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">Enterprise Trust Overview</h2>
          <p className="text-slate-400 mt-1">Real-time analysis of business requests and trust signals.</p>
        </div>
        <div className="flex space-x-3">
          <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 transition-colors text-sm font-medium">
            Export Report
          </button>
          <Link to="/analyzer" className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors text-sm font-medium shadow-glow-sm flex items-center justify-center">
            Scan Inbox Now
          </Link>
        </div>
      </header>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.cards.map((card) => (
          <StatsCard key={card.id} data={card} />
        ))}
      </div>

      {/* Main Grid: Charts & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
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
