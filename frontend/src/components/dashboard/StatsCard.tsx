import React from 'react';
import type { StatCardData } from '../../api/dashboard.api';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface Props {
  data: StatCardData;
}

const StatsCard: React.FC<Props> = ({ data }) => {
  const getTrendIcon = () => {
    if (data.trend === 'up') return <TrendingUp size={16} className="text-green-400" />;
    if (data.trend === 'down') return <TrendingDown size={16} className="text-red-400" />;
    return <Minus size={16} className="text-slate-400" />;
  };

  const getTrendColor = () => {
    if (data.trend === 'up') return 'text-green-400';
    if (data.trend === 'down') return 'text-red-400';
    return 'text-slate-400';
  };

  return (
    <div className="glass-card p-6 flex flex-col group relative overflow-hidden">
      {/* Background Glow on Hover */}
      <div className="absolute -inset-4 bg-gradient-to-r from-cyan-500/0 via-cyan-500/5 to-cyan-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl pointer-events-none"></div>
      
      <div className="flex justify-between items-start relative z-10">
        <span className="text-sm font-medium text-slate-400 uppercase tracking-wider">{data.label}</span>
      </div>
      
      <div className="mt-4 flex items-baseline space-x-3 relative z-10">
        <span className={`text-4xl font-bold ${data.color}`}>{data.value}</span>
        
        <div className={`flex items-center space-x-1 text-sm font-medium ${getTrendColor()}`}>
          {getTrendIcon()}
          <span>{data.change}</span>
        </div>
      </div>
    </div>
  );
};

export default StatsCard;
