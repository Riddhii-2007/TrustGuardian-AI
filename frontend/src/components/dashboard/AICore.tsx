import React, { useEffect, useState } from 'react';
import { ShieldCheck, Cpu, Database, Network } from 'lucide-react';

// ==========================================
// TrustGuardian AI — Futuristic Central AI Core
// Spinning concentric rings, scanning laser lines, and status feed
// ==========================================

export const AICore: React.FC = () => {
  const [activeNodes, setActiveNodes] = useState<number>(142);
  const [decryptionRate, setDecryptionRate] = useState<string>("99.4%");

  useEffect(() => {
    // Generate minor fluctuations for dynamic numbers
    const interval = setInterval(() => {
      setActiveNodes(prev => prev + (Math.random() > 0.5 ? 1 : -1));
      setDecryptionRate((99.2 + Math.random() * 0.5).toFixed(1) + "%");
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="cyber-panel p-6 flex flex-col md:flex-row items-center gap-8 relative overflow-hidden group min-h-[300px]">
      {/* Laser Scanning Grid overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(to_bottom,transparent_49%,rgba(6,182,212,0.08)_50%,transparent_51%)] bg-[length:100%_20px] pointer-events-none"></div>
      
      {/* Animated Laser line */}
      <div className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent opacity-0 group-hover:opacity-100 animate-scanning pointer-events-none"></div>

      {/* Futuristic 3D AI Brain Core */}
      <div className="relative w-44 h-44 shrink-0 flex items-center justify-center">
        {/* Core Outer Rotating Orbit Ring 1 (Clockwise) */}
        <div className="absolute inset-0 rounded-full border border-dashed border-cyan-500/25 animate-rotate-cw scale-100"></div>
        
        {/* Core Outer Rotating Orbit Ring 2 (Counter-Clockwise) */}
        <div className="absolute inset-2 rounded-full border border-dashed border-purple-500/25 animate-rotate-ccw scale-90"></div>

        {/* Orbit Ring 3 with a neon indicator bubble */}
        <div className="absolute inset-6 rounded-full border border-cyan-500/10 animate-rotate-cw">
          <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-cyan-400 rounded-full shadow-[0_0_8px_#06b6d4]"></div>
        </div>

        {/* Orbit Ring 4 with a purple indicator bubble */}
        <div className="absolute inset-10 rounded-full border border-purple-500/10 animate-rotate-ccw">
          <div className="absolute -bottom-1 left-1/3 w-2.5 h-2.5 bg-purple-400 rounded-full shadow-[0_0_8px_#c084fc]"></div>
        </div>

        {/* Glowing pulsing central neural sphere */}
        <div className="absolute w-20 h-20 rounded-full bg-gradient-to-tr from-cyan-600 to-purple-600 flex items-center justify-center animate-core-pulse border border-cyan-400/30">
          <Cpu className="text-white animate-pulse" size={32} />
        </div>
      </div>

      {/* Cybernetic Readout and Metrics Panel */}
      <div className="flex-1 flex flex-col space-y-4 w-full relative z-10">
        <div>
          <div className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-1 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full pulse-dot"></span>
            SYS-INTEL CORE v4.12
          </div>
          <h3 className="text-xl font-bold text-slate-100">Neural Trust Analysis Engine</h3>
        </div>

        {/* Split Parameters list */}
        <div className="grid grid-cols-2 gap-4 border-t border-b border-slate-800/60 py-4">
          <div className="flex items-center space-x-3">
            <Database className="text-purple-400" size={18} />
            <div>
              <div className="text-[10px] font-bold text-slate-500 uppercase">Knowledge Base</div>
              <div className="text-sm font-semibold text-slate-200">{activeNodes} Nodes Graph</div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <ShieldCheck className="text-cyan-400" size={18} />
            <div>
              <div className="text-[10px] font-bold text-slate-500 uppercase">Secure Gateway</div>
              <div className="text-sm font-semibold text-slate-200">PII Mask: 10 Rules</div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <Cpu className="text-green-400" size={18} />
            <div>
              <div className="text-[10px] font-bold text-slate-500 uppercase">Primary Router</div>
              <div className="text-sm font-semibold text-slate-200">Gemini-2.5-Flash</div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <Network className="text-orange-400" size={18} />
            <div>
              <div className="text-[10px] font-bold text-slate-500 uppercase">Accuracy Rate</div>
              <div className="text-sm font-semibold text-slate-200">{decryptionRate} F-Score</div>
            </div>
          </div>
        </div>

        {/* Live Scan Status Log */}
        <div className="bg-slate-950/50 rounded-lg p-3 border border-slate-800/40 text-xs font-mono text-slate-400 flex flex-col space-y-1">
          <div className="flex justify-between">
            <span className="text-slate-500">[SYS_LOG]</span>
            <span className="text-cyan-400">READY</span>
          </div>
          <div className="truncate">Active Ingestion: Gmail API endpoint initialized.</div>
          <div className="truncate">Privacy Guard: Aadhaar, PAN & Routing rules loaded.</div>
        </div>
      </div>
    </div>
  );
};
