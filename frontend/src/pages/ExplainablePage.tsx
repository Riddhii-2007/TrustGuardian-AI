import React, { useState } from 'react';
import { Info, Sparkles, Brain, Award, FileText } from 'lucide-react';

// ==========================================
// TrustGuardian AI — Explainable AI Dashboard
// Explains the reasoning behind risk levels and vector analysis
// ==========================================

interface EvidenceItem {
  id: string;
  source: string;
  weight: number;
  type: 'risk' | 'safety';
  details: string;
}

const ExplainablePage: React.FC = () => {
  const [selectedVector, setSelectedVector] = useState<string>('urgency');

  const vectors = [
    { id: 'urgency', label: 'Urgency Index', value: 88, desc: 'High frequency of pressure keywords demanding immediate action.', color: 'text-red-400', barBg: 'bg-red-500' },
    { id: 'authority', label: 'Authority Impersonation', value: 78, desc: 'Claiming corporate seniority to bypass direct validation paths.', color: 'text-orange-400', barBg: 'bg-orange-500' },
    { id: 'fear', label: 'Fear Induction', value: 45, desc: 'Implying negative consequences or operational downtime if ignored.', color: 'text-yellow-400', barBg: 'bg-yellow-500' },
    { id: 'familiarity', label: 'False Familiarity', value: 30, desc: 'Using colloquial greetings or mimicking internal department styles.', color: 'text-cyan-400', barBg: 'bg-cyan-500' },
    { id: 'intent', label: 'Malicious Intent', value: 85, desc: 'Core request redirects to wiring or modifying system configurations.', color: 'text-pink-400', barBg: 'bg-pink-500' }
  ];

  const evidenceList: EvidenceItem[] = [
    { id: 'ev-1', source: 'Domain reputation lookup', weight: 95, type: 'risk', details: 'Sender domain matches trustguardian.ai closely but has subtle typo (e.g. trustgardian).' },
    { id: 'ev-2', source: 'PII Shield Scan', weight: 80, type: 'risk', details: 'Direct reference to updating a direct deposit routing path detected in the email body.' },
    { id: 'ev-3', source: 'Language Parsing Model', weight: 90, type: 'risk', details: 'Command verbs (wire, immediately, bypass, urgent) grouped with high density.' },
    { id: 'ev-4', source: 'SPF / DKIM Signatures', weight: 100, type: 'safety', details: 'Sender SPF headers passed verification, indicating a valid server origin.' }
  ];

  const currentVector = vectors.find(v => v.id === selectedVector) || vectors[0];

  return (
    <div className="space-y-8 animate-fade-in pb-8">
      <header>
        <h2 className="text-3xl font-extrabold text-slate-100 flex items-center gap-3 tracking-tight">
          <Brain className="text-cyan-400" /> Explainable AI (XAI)
        </h2>
        <p className="text-base text-slate-400 mt-2">Inspect vector weights, matching indicators, and logical decisions.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Side: Vectors List */}
        <div className="cyber-panel space-y-6">
          <h3 className="text-lg font-bold text-slate-200 border-b border-slate-800/40 pb-3 flex items-center gap-2">
            <Sparkles size={18} className="text-cyan-400" />
            Psychological Vectors
          </h3>

          <div className="space-y-3">
            {vectors.map(vector => (
              <button 
                key={vector.id}
                onClick={() => setSelectedVector(vector.id)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all duration-200 flex flex-col space-y-2 clickable ${
                  selectedVector === vector.id 
                    ? 'bg-slate-900/60 border-cyan-500/50 shadow-glow-sm' 
                    : 'bg-slate-950/40 border-slate-900 hover:border-slate-800'
                }`}
              >
                <div className="flex justify-between items-center w-full">
                  <span className="text-xs font-bold text-slate-300">{vector.label}</span>
                  <span className={`text-xs font-mono font-extrabold ${vector.color}`}>{vector.value}%</span>
                </div>
                <div className="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden">
                  <div className={`h-full ${vector.barBg}`} style={{ width: `${vector.value}%` }} />
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Center: Vector Focus details */}
        <div className="cyber-panel flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-200 border-b border-slate-800/40 pb-3 flex items-center gap-2">
              <Info size={18} className="text-cyan-400" />
              Focus Analysis
            </h3>
            <div className="mt-6 space-y-4">
              <div className="text-2xl font-extrabold text-slate-100">{currentVector.label}</div>
              <div className={`text-4xl font-mono font-extrabold ${currentVector.color}`}>
                {currentVector.value}% Confidence
              </div>
              <p className="text-sm text-slate-400 leading-relaxed mt-4">
                {currentVector.desc}
              </p>
            </div>
          </div>

          <div className="mt-8 bg-slate-950/40 border border-slate-900 rounded-xl p-4 flex items-center gap-3">
            <Award className="text-cyan-400 flex-shrink-0" size={24} />
            <div className="text-xs text-slate-400 leading-relaxed">
              <strong>Forensic Indicator:</strong> This score represents the mathematical density of patterns matched by our custom language heuristics.
            </div>
          </div>
        </div>

        {/* Right Side: Evidence cards */}
        <div className="cyber-panel space-y-6">
          <h3 className="text-lg font-bold text-slate-200 border-b border-slate-800/40 pb-3 flex items-center gap-2">
            <FileText size={18} className="text-cyan-400" />
            Decision Evidence
          </h3>

          <div className="space-y-4 max-h-[360px] overflow-auto pr-1">
            {evidenceList.map(ev => (
              <div 
                key={ev.id}
                className={`p-4 rounded-xl border flex flex-col space-y-2 relative overflow-hidden ${
                  ev.type === 'risk' 
                    ? 'bg-red-950/5 border-red-500/10' 
                    : 'bg-green-950/5 border-green-500/10'
                }`}
              >
                <div className="flex justify-between items-center z-10">
                  <span className="text-xs font-bold text-slate-300">{ev.source}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${
                    ev.type === 'risk' 
                      ? 'bg-red-500/10 border-red-500/20 text-red-400' 
                      : 'bg-green-500/10 border-green-500/20 text-green-400'
                  }`}>
                    {ev.type === 'risk' ? 'Anomaly' : 'Safe Sign'}
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed z-10">
                  {ev.details}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExplainablePage;
