import React from 'react';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Tooltip } from 'recharts';
import type { PsychologyFactors } from '../../api/requests.api';

interface Props {
  factors: PsychologyFactors;
}

const PsychologyRadar: React.FC<Props> = ({ factors }) => {
  // Transform data for Recharts
  const data = [
    { subject: 'Urgency', A: factors.urgency * 100 },
    { subject: 'Authority', A: factors.authority * 100 },
    { subject: 'Fear', A: factors.fear * 100 },
    { subject: 'Familiarity', A: factors.familiarity * 100 },
    { subject: 'Intent', A: factors.intent * 100 },
  ];

  return (
    <div className="w-full h-full min-h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#1e293b" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#0f1629', 
              borderColor: '#1e293b',
              borderRadius: '8px',
              color: '#f8fafc'
            }}
            itemStyle={{ color: '#06b6d4' }}
            formatter={(value: number) => [`${value.toFixed(0)}%`, 'Score']}
          />
          <Radar
            name="Psychology"
            dataKey="A"
            stroke="#06b6d4"
            fill="#06b6d4"
            fillOpacity={0.4}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PsychologyRadar;
