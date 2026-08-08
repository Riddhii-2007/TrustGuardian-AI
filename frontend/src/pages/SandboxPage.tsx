import React, { useState, useEffect } from 'react';
import { Play, RotateCcw, Sliders, Shield, ShieldCheck, ShieldAlert, Cpu, Layers, FileText, AlertTriangle } from 'lucide-react';
import { requestsApi, SimulationResult } from '../api/requests.api';

interface PipelineStep {
  name: string;
  status: 'idle' | 'active' | 'success' | 'fail';
  description: string;
  icon: React.ReactNode;
}

const SandboxPage: React.FC = () => {
  // Try to load recent analysis from localStorage
  const [recentAnalysis, setRecentAnalysis] = useState<any>(null);
  const [isDemoData, setIsDemoData] = useState<boolean>(true);

  // Parameter Controls
  const [trustScore, setTrustScore] = useState<number>(82);
  const [confidenceScore, setConfidenceScore] = useState<number>(85);
  const [recommendation, setRecommendation] = useState<string>('ALLOW');
  const [flags, setFlags] = useState<string[]>([]);

  // Simulation Status
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [activeStep, setActiveStep] = useState<number>(-1);
  const [apiResult, setApiResult] = useState<SimulationResult | null>(null);

  useEffect(() => {
    try {
      const stored = localStorage.getItem('recent_analysis');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed && parsed.analysis) {
          setRecentAnalysis(parsed);
          setIsDemoData(false);
          setTrustScore(parsed.analysis.trust_score ?? 82);
          setConfidenceScore(parsed.analysis.confidence_score ?? 85);
          setRecommendation(parsed.analysis.recommendation ?? 'ALLOW');
          setFlags(parsed.analysis.flags ?? []);
        }
      }
    } catch (err) {
      console.error('Failed to load recent analysis:', err);
    }
  }, []);

  // Pipeline steps
  const steps: PipelineStep[] = [
    { name: 'Ingestion Portal', status: activeStep > 0 ? 'success' : activeStep === 0 ? 'active' : 'idle', description: 'Gmail API sync parsing raw headers.', icon: <FileText size={18} /> },
    { name: 'PII Redactor', status: activeStep > 1 ? 'success' : activeStep === 1 ? 'active' : 'idle', description: 'Redacting Aadhaar, PAN & Routing info.', icon: <Layers size={18} /> },
    { name: 'Threat Intel Core', status: activeStep > 2 ? 'success' : activeStep === 2 ? 'active' : 'idle', description: 'Domain reputation lookup.', icon: <Cpu size={18} /> },
    { name: 'Trust Engine Eval', status: activeStep > 3 ? 'success' : activeStep === 3 ? 'active' : 'idle', description: 'Calculating final vector weights.', icon: <Shield size={18} /> }
  ];

  const runSimulation = async () => {
    if (isSimulating) return;
    setIsSimulating(true);
    setApiResult(null);
    setActiveStep(0);

    try {
      // Fetch simulation result from the backend
      const result = await requestsApi.simulateOutcome({
        request_id: recentAnalysis?.id || "demo-request",
        action: "simulate",
        parameters: {},
        trust_score: trustScore,
        confidence_score: confidenceScore,
        recommendation: recommendation,
        flags: flags
      });

      // Step transition animation
      let stepIndex = 0;
      const stepInterval = setInterval(() => {
        stepIndex++;
        if (stepIndex >= 4) {
          clearInterval(stepInterval);
          setIsSimulating(false);
          setApiResult(result);
          setActiveStep(4);
        } else {
          setActiveStep(stepIndex);
        }
      }, 600);

    } catch (err) {
      console.error('Simulation API call failed:', err);
      setIsSimulating(false);
      setActiveStep(-1);
    }
  };

  const resetSimulation = () => {
    setIsSimulating(false);
    setApiResult(null);
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

      {/* Warning/Honesty Banner */}
      {isDemoData ? (
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 text-amber-400 flex items-start gap-3 shadow-[0_0_20px_rgba(245,158,11,0.02)]">
          <AlertTriangle className="shrink-0 mt-0.5" size={18} />
          <div>
            <div className="font-bold text-sm text-slate-200">No analysis loaded — showing example simulation</div>
            <div className="text-xs text-slate-400 mt-1">
              Go to the <span className="font-semibold text-cyan-400">AI Analyzer</span> page and run a scan to inject live corporate request parameters here.
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4 text-green-400 flex items-start gap-3 shadow-[0_0_20px_rgba(34,197,94,0.02)]">
          <ShieldCheck className="shrink-0 mt-0.5" size={18} />
          <div>
            <div className="font-bold text-sm text-slate-200">Loaded recent analysis parameters</div>
            <div className="text-xs text-slate-400 mt-1">
              Subject: <span className="font-semibold text-slate-300">{recentAnalysis.title || 'Untitled Request'}</span> | Sender: <span className="font-semibold text-slate-300">{recentAnalysis.requester}</span>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Parameters Sliders panel */}
        <div className="cyber-panel space-y-6">
          <h3 className="text-lg font-bold text-slate-200 border-b border-slate-800/40 pb-3 flex items-center gap-2">
            <Sliders size={18} className="text-cyan-400" />
            Parameter Controls
          </h3>

          <div className="space-y-6">
            {/* Slider 1: Trust Score */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-400">Trust Score</span>
                <span className="text-cyan-400">{trustScore}%</span>
              </div>
              <input 
                type="range" 
                min="0" 
                max="100" 
                value={trustScore} 
                onChange={(e) => setTrustScore(Number(e.target.value))}
                className="w-full h-1 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-cyan-500"
              />
            </div>

            {/* Slider 2: Confidence Score */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-400">Confidence Score</span>
                <span className="text-cyan-400">{confidenceScore}%</span>
              </div>
              <input 
                type="range" 
                min="0" 
                max="100" 
                value={confidenceScore} 
                onChange={(e) => setConfidenceScore(Number(e.target.value))}
                className="w-full h-1 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-cyan-500"
              />
            </div>

            {/* Dropdown 3: Recommendation Policy */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 block">Policy Recommendation</label>
              <select
                value={recommendation}
                onChange={(e) => setRecommendation(e.target.value)}
                className="w-full bg-slate-950/60 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500/50"
              >
                <option value="ALLOW">ALLOW</option>
                <option value="VERIFY_UNVERIFIED_SENDER">VERIFY_UNVERIFIED_SENDER</option>
                <option value="BLOCK">BLOCK</option>
                <option value="BLOCK_ESCALATE_SOC">BLOCK_ESCALATE_SOC</option>
              </select>
            </div>

            {/* Flags Visualizer */}
            <div className="space-y-2 pt-2">
              <label className="text-xs font-semibold text-slate-400 block">Active Threats/Flags ({flags.length})</label>
              {flags.length > 0 ? (
                <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
                  {flags.map((flag, idx) => (
                    <span key={idx} className="px-2 py-1 bg-red-500/10 border border-red-500/20 text-red-400 rounded-md text-[10px] font-bold">
                      {flag}
                    </span>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-slate-500 italic bg-slate-950/20 border border-slate-900 rounded-lg p-3 text-center">
                  No threat flags active.
                </div>
              )}
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
            {!apiResult ? (
              <div className="bg-slate-950/40 rounded-xl p-4 border border-slate-900 text-slate-500 text-sm font-semibold flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-slate-600 animate-pulse"></span>
                {isSimulating ? 'Processing simulation pipelines...' : 'Awaiting pipeline simulation trigger...'}
              </div>
            ) : (
              <div className="space-y-4">
                {/* Recommendation summary badge */}
                <div className={`rounded-xl p-4 border flex items-start gap-3 ${
                  apiResult.recommendation.includes("BLOCK") 
                    ? "bg-red-500/5 border-red-500/20 text-red-400 shadow-[0_0_20px_rgba(239,68,68,0.05)]"
                    : apiResult.recommendation.includes("VERIFY")
                      ? "bg-amber-500/5 border-amber-500/20 text-amber-400 shadow-[0_0_20px_rgba(245,158,11,0.05)]"
                      : "bg-green-500/5 border-green-500/20 text-green-400 shadow-[0_0_20px_rgba(34,197,94,0.05)]"
                }`}>
                  <div className="shrink-0 mt-0.5">
                    {apiResult.recommendation.includes("BLOCK") ? (
                      <ShieldAlert size={20} />
                    ) : (
                      <ShieldCheck size={20} />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-bold text-slate-200">{apiResult.recommendation}</div>
                    <div className="text-xs text-slate-400 mt-1">
                      Parameters checked: Trust {trustScore}% | Confidence {confidenceScore}% | Recommendation: {recommendation}
                    </div>
                  </div>
                </div>

                {/* Scenario details */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {apiResult.scenarios.map((scen, idx) => (
                    <div key={idx} className="bg-slate-950/60 border border-slate-900 rounded-xl p-4 flex flex-col justify-between">
                      <div>
                        <div className="flex justify-between items-start mb-2">
                          <span className="px-2 py-0.5 bg-slate-900 border border-slate-800 text-[10px] font-bold text-slate-400 rounded">
                            Scenario {scen.scenario_id.toUpperCase()}
                          </span>
                          <span className="text-[11px] font-semibold text-cyan-400">
                            {Math.round(scen.probability * 100)}% Probability
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed">{scen.description}</p>
                      </div>
                      <div className="mt-4 pt-3 border-t border-slate-900/60 flex justify-between items-center text-xs">
                        <span className="text-slate-500">Business Impact Risk</span>
                        <span className={`font-bold ${
                          scen.impact_score > 70 
                            ? "text-red-400" 
                            : scen.impact_score > 30 
                              ? "text-amber-400" 
                              : "text-green-400"
                        }`}>
                          {scen.impact_score} / 100
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SandboxPage;
