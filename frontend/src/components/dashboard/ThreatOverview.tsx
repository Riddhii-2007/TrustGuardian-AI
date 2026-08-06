import React from 'react';
import type { ThreatCategory } from '../../api/dashboard.api';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from 'recharts';

interface Props {
  threats: ThreatCategory[];
}

const ThreatOverview: React.FC<Props> = ({ threats }) => {
  return (
    <div className="glass-card p-6 h-full flex flex-col">
      <h3 className="text-lg font-bold text-slate-100 mb-6">Threat Vectors Overview</h3>
      
      <div className="flex-1 w-full min-h-[250px]">
        {threats.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-500">
            No threat data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={threats}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#1e293b" />
              <XAxis type="number" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis 
                type="category" 
                dataKey="name" 
                stroke="#94a3b8" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false}
                width={120}
              />
              <Tooltip 
                cursor={{ fill: 'rgba(30, 41, 59, 0.5)' }}
                contentStyle={{ 
                  backgroundColor: '#0f1629', 
                  borderColor: '#1e293b',
                  borderRadius: '8px',
                  color: '#f8fafc'
                }}
                itemStyle={{ color: '#06b6d4' }}
              />
              <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={24}>
                {threats.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

export default ThreatOverview;
