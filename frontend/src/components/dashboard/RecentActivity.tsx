import React from 'react';
import type { ActivityItem } from '../../api/dashboard.api';
import { ShieldAlert, Cpu, Activity } from 'lucide-react';

interface Props {
  activities: ActivityItem[];
}

const RecentActivity: React.FC<Props> = ({ activities }) => {
  
  const getIcon = (type: string, risk_level: string) => {
    let colorClass = 'text-slate-400 bg-slate-800';
    
    if (risk_level === 'critical') colorClass = 'text-red-400 bg-red-500/10 border-red-500/30';
    else if (risk_level === 'high') colorClass = 'text-orange-400 bg-orange-500/10 border-orange-500/30';
    else if (risk_level === 'medium') colorClass = 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
    else if (risk_level === 'safe') colorClass = 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30';

    const baseClasses = `w-10 h-10 rounded-lg border flex items-center justify-center shadow-sm ${colorClass}`;

    switch (type) {
      case 'alert':
        return <div className={baseClasses}><ShieldAlert size={20} /></div>;
      case 'analysis':
        return <div className={baseClasses}><Cpu size={20} /></div>;
      case 'workflow':
        return <div className={baseClasses}><Activity size={20} /></div>;
      default:
        return <div className={baseClasses}><Activity size={20} /></div>;
    }
  };

  return (
    <div className="glass-card p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-slate-100">Recent Activity</h3>
        <button className="text-sm font-medium text-cyan-400 hover:text-cyan-300 transition-colors">
          View All
        </button>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 space-y-6">
        {activities.length === 0 ? (
          <div className="text-center text-slate-500 py-8">No recent activity found.</div>
        ) : (
          activities.map((activity) => (
            <div key={activity.id} className="flex gap-4 relative group cursor-pointer">
              {/* Timeline Connector */}
              <div className="absolute top-10 left-5 bottom-[-24px] w-px bg-slate-700 group-last:hidden"></div>
              
              <div className="shrink-0 relative z-10">
                {getIcon(activity.type, activity.risk_level)}
              </div>
              
              <div className="flex-1 pb-1">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="text-sm font-semibold text-slate-200 group-hover:text-cyan-400 transition-colors">
                    {activity.title}
                  </h4>
                  <span className="text-xs text-slate-500 font-mono">{activity.timestamp}</span>
                </div>
                <p className="text-sm text-slate-400 line-clamp-2 leading-relaxed">
                  {activity.description}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default RecentActivity;
