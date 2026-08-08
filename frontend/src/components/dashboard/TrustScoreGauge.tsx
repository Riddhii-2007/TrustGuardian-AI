import React from 'react';

// ==========================================
// TrustGuardian AI — Circular Trust Gauge
// SVG-based glowing ring gauge with dynamic color shifting
// ==========================================

interface Props {
  score: number | null;        // Overall trust score (0 - 100) or null for N/A
  confidence: number | null;   // Confidence percentage (0 - 100) or null for N/A
  riskLevel: string;    // "Critical" | "High" | "Medium" | "Low" | "N/A"
}

export const TrustScoreGauge: React.FC<Props> = ({ score, confidence, riskLevel }) => {
  // SVG Ring values
  const radius = 70;
  const strokeWidth = 10;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = score !== null ? circumference - (score / 100) * circumference : circumference;

  // Determine colors based on risk/trust levels
  const getColors = () => {
    if (score === null || riskLevel === 'N/A') {
      return {
        text: 'text-slate-500',
        stroke: 'stroke-slate-800/60',
        glow: 'transparent',
        bg: 'bg-slate-800/10 border-slate-800/20'
      };
    }
    const lvl = riskLevel.toLowerCase();
    if (lvl === 'critical' || score < 40) {
      return {
        text: 'text-red-500',
        stroke: 'stroke-red-500',
        glow: 'rgba(239, 68, 68, 0.4)',
        bg: 'bg-red-500/10 border-red-500/20'
      };
    }
    if (lvl === 'high' || lvl === 'medium' || score < 75) {
      return {
        text: 'text-yellow-500',
        stroke: 'stroke-yellow-500',
        glow: 'rgba(234, 179, 8, 0.4)',
        bg: 'bg-yellow-500/10 border-yellow-500/20'
      };
    }
    return {
      text: 'text-cyan-400',
      stroke: 'stroke-cyan-400',
      glow: 'rgba(6, 182, 212, 0.4)',
      bg: 'bg-cyan-500/10 border-cyan-500/20'
    };
  };

  const currentColors = getColors();

  return (
    <div className="cyber-panel p-6 flex flex-col items-center justify-center min-h-[300px] relative overflow-hidden group">
      {/* Background radial highlight */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(6,182,212,0.02)_0%,transparent_70%)] pointer-events-none"></div>

      <div className="relative w-44 h-44 flex items-center justify-center">
        {/* SVG Circle Dial */}
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 160 160">
          {/* Faint Outer Ring track */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            strokeWidth={strokeWidth}
            className="stroke-slate-800/80 fill-transparent"
          />
          {/* Active Progress Ring with shadow glow */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            strokeWidth={strokeWidth}
            className={`${currentColors.stroke} fill-transparent transition-all duration-1000 ease-out`}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{
              filter: `drop-shadow(0 0 6px ${currentColors.glow})`,
            }}
          />
        </svg>

        {/* Center content metrics */}
        <div className="absolute flex flex-col items-center justify-center text-center">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">TRUST INDEX</span>
          <span className={`text-4xl font-extrabold tracking-tight ${currentColors.text} mt-1`}>
            {score !== null ? score : 'N/A'}
          </span>
          {score !== null && <span className="text-xs text-slate-400 font-semibold mt-1">/ 100</span>}
        </div>
      </div>

      {/* Trust Metrics Readout */}
      <div className="w-full flex items-center justify-between mt-6 border-t border-slate-800/60 pt-4 px-2">
        <div className="text-center">
          <div className="text-[10px] font-bold text-slate-500 uppercase">Confidence</div>
          <div className="text-sm font-bold text-slate-200 mt-1">
            {confidence !== null ? `${confidence}%` : 'N/A'}
          </div>
        </div>

        <div className="w-px h-8 bg-slate-800"></div>

        <div className="text-center">
          <div className="text-[10px] font-bold text-slate-500 uppercase">Risk Level</div>
          <div className={`text-xs font-extrabold uppercase mt-1.5 px-2 py-0.5 rounded border ${currentColors.bg} ${currentColors.text}`}>
            {riskLevel}
          </div>
        </div>
      </div>
    </div>
  );
};
