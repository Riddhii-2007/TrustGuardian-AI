import React, { useEffect, useState } from 'react';
import { Mail, Shield, ShieldAlert, Cpu, Network, CheckCircle, Database, FileText } from 'lucide-react';

// ==========================================
// TrustGuardian AI — Processing Pipeline
// Sequentially lights up stages, traveling glow lines, and check ticks
// ==========================================

interface Stage {
  label: string;
  desc: string;
  icon: React.ReactNode;
}

export const AIAnalysisPipeline: React.FC = () => {
  const [currentStage, setCurrentStage] = useState(0);

  const stages: Stage[] = [
    { label: 'Request Ingestion', desc: 'Parsing email payloads and header trails', icon: <Mail size={18} /> },
    { label: 'Security Masking', desc: 'Anonymizing PII: PAN cards, Aadhaar, names', icon: <Shield size={18} /> },
    { label: 'Threat Intel Sync', desc: 'Checking domain reputations and link integrity', icon: <ShieldAlert size={18} /> },
    { label: 'Neo4j Graph Context', desc: 'Querying AuraDB for threat node correlations', icon: <Network size={18} /> },
    { label: 'LLM Router Dispatch', desc: 'Initiating reasoning pathways in Gemini-2.5', icon: <Cpu size={18} /> },
    { label: 'Trust Decision Engine', desc: 'Synthesizing weight parameters and trust signals', icon: <Database size={18} /> },
    { label: 'Fusing Evidence Report', desc: 'Assembling natural language explanations', icon: <FileText size={18} /> }
  ];

  useEffect(() => {
    // Sequentially progress steps
    const interval = setInterval(() => {
      setCurrentStage(prev => {
        if (prev < stages.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 700);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="cyber-panel p-6 w-full flex flex-col space-y-4">
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs font-bold text-cyan-400 tracking-wider uppercase flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 pulse-dot"></span>
          SECURE AI GATEWAY ACTIVE
        </span>
        <span className="text-xs text-slate-500 font-mono font-semibold">STAGE {currentStage + 1} OF 7</span>
      </div>

      <div className="flex flex-col space-y-6 relative pl-10 before:absolute before:left-4.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800/60">
        {/* Dynamic laser travel line */}
        <div 
          className="absolute left-4.5 top-2 w-0.5 bg-gradient-to-b from-cyan-400 to-transparent transition-all duration-500"
          style={{ height: `${(currentStage / (stages.length - 1)) * 96}%` }}
        />

        {stages.map((stage, idx) => {
          const isCompleted = idx < currentStage;
          const isActive = idx === currentStage;

          let statusColor = 'border-slate-800 text-slate-500 bg-slate-950/40';
          let borderGlow = '';

          if (isCompleted) {
            statusColor = 'border-green-500/40 text-green-400 bg-green-950/20';
            borderGlow = 'shadow-[0_0_12px_rgba(34,197,94,0.15)]';
          } else if (isActive) {
            statusColor = 'border-cyan-500/40 text-cyan-400 bg-cyan-950/20 animate-pulse';
            borderGlow = 'shadow-[0_0_15px_rgba(6,182,212,0.25)]';
          }

          return (
            <div key={idx} className="flex items-start space-x-4 relative transition-all duration-300">
              {/* Pipeline nodes */}
              <div className={`w-9 h-9 rounded-lg border flex items-center justify-center shrink-0 z-10 ${statusColor} ${borderGlow}`}>
                {isCompleted ? <CheckCircle size={16} /> : stage.icon}
              </div>

              {/* Pipeline details */}
              <div className="flex-1 min-w-0">
                <h4 className={`text-sm font-bold transition-colors ${isActive ? 'text-cyan-300' : isCompleted ? 'text-green-300' : 'text-slate-500'}`}>
                  {stage.label}
                </h4>
                <p className={`text-xs mt-0.5 transition-colors ${isActive ? 'text-slate-300' : 'text-slate-500'}`}>
                  {stage.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
