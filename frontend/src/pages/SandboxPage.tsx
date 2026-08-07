import React, { useState } from 'react';
import { Play, RotateCcw, Sliders, Shield, ShieldCheck, ShieldAlert, Cpu, Layers, FileText } from 'lucide-react';

// ==========================================
// TrustGuardian AI — Decision Sandbox
// Simulates threat policy pipelines with interactive parameters
// ==========================================

interface PipelineStep {
  name: string;
  status: 'idle' | 'active' | 'success' | 'fail';
  description: string;
  icon: React.ReactNode;
}

const SandboxPage: React.FC = () => {
  // Simulator Controls
  const [modelConfidence, setModelConfidence] = useState<number>(85);
  const [trustThreshold, setTrustThreshold] = useState<number>(75);
  const [urgencyWeight, setUrgencyWeight] = useState<number>(60);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<'idle' | 'authorized' | 'blocked'>('idle');
  const [activeStep, setActiveStep] = useState<number>(-1);

  // Pipeline steps
  const steps: PipelineStep[] = [
    { name: 'Ingestion Portal', status: activeStep > 0 ? 'success' : activeStep === 0 ? 'active' : 'idle', description: 'Gmail API sync parsing raw headers.', icon: <FileText size={18} /> },
    { name: 'PII Redactor', status: activeStep > 1 ? 'success' : activeStep === 1 ? 'active' : 'idle', description: 'Redacting Aadhaar, PAN & Routing info.', icon: <Layers size={18} /> },
    { name: 'Threat Intel Core', status: activeStep > 2 ? 'success' : activeStep === 2 ? 'active' : 'idle', description: 'Domain reputation lookup.', icon: <Cpu size={18} /> },
    { name: 'Trust Engine Eval', status: activeStep > 3 ? 'success' : activeStep === 3 ? 'active' : 'idle', description: 'Calculating final vector weights.', icon: <Shield size={18} /> }
  ];

  const runSimulation = () => {
    if (isSimulating) return;
    setIsSimulating(true);
    setSimulationResult('idle');
    setActiveStep(0);

    const stepInterval = setInterval(() => {
      setActiveStep((prev) => {
        if (prev >= 3) {
          clearInterval(stepInterval);
          setIsSimulating(false);
          // Evaluate mock outcome based on settings
          const computedScore = 100 - (urgencyWeight * 0.4) + (modelConfidence * 0.2);
          if (computedScore >= trustThreshold) {
            setSimulationResult('authorized');
          } else {
            setSimulationResult('blocked');
          }
          return 4;
        }
        return prev + 1;
      });
    }, 1000);
  };

  const resetSimulation = () => {
    setIsSimulating(false);
    setSimulationResult('idle');
    setActiveStep(-1);
  };

  return (
    <div className="space-y-8 animate-fade-in pb-8">
      <header>
        <h2 className="text-3xl font-extrabold text-slate-100 flex items-center gap-3 tracking-tight">
          <Play className="text-cyan-400" /> Policy Decision Sandbox
        </h2>
        <p className="text-base text-slate-400 mt-2">Adjust security weights and simulate pipeline processing resolutions.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Parameters Sliders panel */}
        <div className="cyber-panel space-y-6">
          <h3 className="text-lg font-bold text-slate-200 border-b border-slate-800/40 pb-3 flex items-center gap-2">
            <Sliders size={18} className="text-cyan-400" />
            Parameter Controls
          </h3>

          <div className="space-y-5">
            {/* Slider 1 */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-400">Model Confidence Limit</span>
                <span className="text-cyan-400">{modelConfidence}%</span>
              </div>
              <input 
                type="range" 
                min="50" 
                max="100" 
                value={modelConfidence} 
                onChange={(e) => setModelConfidence(Number(e.target.value))}
                className="w-full h-1 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-cyan-500"
              />
            </div>

            {/* Slider 2 */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-400">Min Trust Auth Threshold</span>
                <span className="text-cyan-400">{trustThreshold}%</span>
              </div>
              <input 
                type="range" 
                min="30" 
                max="95" 
                value={trustThreshold} 
                onChange={(e) => setTrustThreshold(Number(e.target.value))}
                className="w-full h-1 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-cyan-500"
              />
            </div>

            {/* Slider 3 */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-400">BEC Urgency Weight Penalty</span>
                <span className="text-cyan-400">{urgencyWeight}%</span>
              </div>
              <input 
                type="range" 
                min="10" 
                max="100" 
                value={urgencyWeight} 
                onChange={(e) => setUrgencyWeight(Number(e.target.value))}
                className="w-full h-1 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-cyan-500"
              />
            </div>
          </div>

          <div className="flex space-x-3 pt-4">
            <button 
              onClick={runSimulation}
              disabled={isSimulating}
              className={`flex-1 py-2.5 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all duration-200 ${
                isSimulating 
                  ? 'bg-cyan-950/20 text-cyan-700 border border-cyan-950 cursor-not-allowed' 
                  : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-glow-sm clickable'
              }`}
            >
              <Play size={16} />
              Run Pipeline
            </button>
            <button 
              onClick={resetSimulation}
              className="px-4 py-2.5 bg-slate-900/60 hover:bg-slate-800/80 text-slate-300 rounded-xl border border-slate-800 transition-all duration-200 text-sm font-semibold flex items-center justify-center clickable"
            >
              <RotateCcw size={16} />
            </button>
          </div>
        </div>

        {/* Live branching paths simulator canvas */}
        <div className="lg:col-span-2 cyber-panel flex flex-col justify-between relative overflow-hidden">
          {/* Animated Background Laser lines */}
          {isSimulating && (
            <div className="absolute inset-0 z-0 bg-[radial-gradient(ellipse_at_center,rgba(6,182,212,0.03),transparent_60%)] pointer-events-none" />
          )}

          <div className="relative z-10">
            <h3 className="text-lg font-bold text-slate-200 border-b border-slate-800/40 pb-3 flex items-center gap-2">
              <Cpu size={18} className="text-cyan-400" />
              Dynamic Execution Pipeline
            </h3>

            {/* Steps execution blocks */}
            <div className="mt-8 flex flex-col space-y-6 relative">
              {steps.map((step, idx) => (
                <div key={idx} className="flex items-start space-x-4 relative">
                  {/* Step Connector Line */}
                  {idx < steps.length - 1 && (
                    <div className="absolute left-[17px] top-[34px] w-[2px] h-[34px] bg-slate-800/60 overflow-hidden">
                      <div className={`w-full h-1/2 bg-cyan-400 absolute top-0 left-0 animate-ping ${
                        activeStep === idx ? 'block' : 'hidden'
                      }`} />
                    </div>
                  )}

                  {/* Icon Node */}
                  <div className={`w-9 h-9 rounded-lg border flex items-center justify-center transition-all duration-300 z-10 ${
                    step.status === 'active' 
                      ? 'bg-cyan-500/10 border-cyan-400 text-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.25)]' 
                      : step.status === 'success'
                        ? 'bg-green-500/10 border-green-500/30 text-green-400'
                        : 'bg-slate-950 border-slate-800 text-slate-500'
                  }`}>
                    {step.icon}
                  </div>

                  {/* Details */}
                  <div className="flex-1">
                    <h4 className={`text-sm font-bold transition-all duration-300 ${
                      step.status === 'active' ? 'text-cyan-400 font-extrabold' : 'text-slate-300'
                    }`}>
                      {step.name}
                    </h4>
                    <p className="text-xs text-slate-500 mt-1">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Outcome resolution card */}
          <div className="relative z-10 mt-8 pt-6 border-t border-slate-800/40">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Decision Resolution</h4>
            {simulationResult === 'idle' ? (
              <div className="bg-slate-950/40 rounded-xl p-4 border border-slate-900 text-slate-500 text-sm font-semibold flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-slate-600 animate-pulse"></span>
                Awaiting pipeline simulation trigger...
              </div>
            ) : simulationResult === 'authorized' ? (
              <div className="bg-green-500/5 rounded-xl p-4 border border-green-500/20 text-green-400 flex items-center justify-between shadow-[0_0_20px_rgba(34,197,94,0.05)]">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-green-500/10 flex items-center justify-center border border-green-500/30">
                    <ShieldCheck size={20} />
                  </div>
                  <div>
                    <div className="text-sm font-bold text-slate-200">Authorized Transaction</div>
                    <div className="text-xs text-slate-400 mt-0.5">Trust Score is above authorization limit. Passes corporate guidelines.</div>
                  </div>
                </div>
                <span className="px-3 py-1 bg-green-500/10 border border-green-500/30 text-[10px] font-extrabold uppercase rounded-md tracking-wider">
                  SAFE
                </span>
              </div>
            ) : (
              <div className="bg-red-500/5 rounded-xl p-4 border border-red-500/20 text-red-400 flex items-center justify-between shadow-[0_0_20px_rgba(239,68,68,0.05)]">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center border border-red-500/30">
                    <ShieldAlert size={20} />
                  </div>
                  <div>
                    <div className="text-sm font-bold text-slate-200">Blocked Wire Transfer</div>
                    <div className="text-xs text-slate-400 mt-0.5">BEC high risk detected due to urgency weights. Blocked automatically.</div>
                  </div>
                </div>
                <span className="px-3 py-1 bg-red-500/10 border border-red-500/30 text-[10px] font-extrabold uppercase rounded-md tracking-wider">
                  BLOCKED
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SandboxPage;
