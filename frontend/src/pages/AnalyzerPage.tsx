import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { requestsApi } from '../api/requests.api';
import PsychologyRadar from '../components/analyzer/PsychologyRadar';
import { AlertTriangle, ShieldCheck, ShieldAlert, AlertCircle, Bot, Loader2 } from 'lucide-react';
import { AIAnalysisPipeline } from '../components/analyzer/AIAnalysisPipeline';

// ===================================
// TrustGuardian AI — Analyzer Sandbox
// ===================================

const AnalyzerPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  
  // Hardcoded for demo purposes if no ID is provided, else fetch by ID
  // In a real app, we'd list them and click into them.
  const isDemo = !id || id === 'demo';

  const [demoInput, setDemoInput] = useState(
    "Hi John, I need you to wire $50,000 to the attached vendor immediately. I'm in a meeting and can't take calls. Please process this urgently so we don't lose the contract. - CEO"
  );

  const { data: requestData, isLoading: isFetching } = useQuery({
    queryKey: ['request', id],
    queryFn: () => requestsApi.getRequestById(id!),
    enabled: !isDemo,
  });

  const analyzeMutation = useMutation({
    mutationFn: (text: string) => requestsApi.analyzeRequest(text, "Urgent Wire Transfer", "ceo-imposter@trust-guardian.ai"),
  });

  const handleAnalyze = () => {
    analyzeMutation.mutate(demoInput);
  };

  const currentData = isDemo ? analyzeMutation.data : requestData;
  const isLoading = isFetching || analyzeMutation.isPending;

  React.useEffect(() => {
    if (currentData) {
      localStorage.setItem('recent_analysis', JSON.stringify(currentData));
    }
  }, [currentData]);

  const getRiskIcon = (level: string | undefined) => {
    switch (level?.toLowerCase()) {
      case 'critical': return <ShieldAlert className="text-red-500" size={32} />;
      case 'high': return <AlertTriangle className="text-orange-500" size={32} />;
      case 'medium': return <AlertCircle className="text-yellow-500" size={32} />;
      default: return <ShieldCheck className="text-green-500" size={32} />;
    }
  };

  const getRiskColor = (level: string | undefined) => {
    switch (level?.toLowerCase()) {
      case 'critical': return 'text-red-500';
      case 'high': return 'text-orange-500';
      case 'medium': return 'text-yellow-500';
      default: return 'text-green-500';
    }
  };

  return (
    <div className="h-full flex flex-col space-y-6 animate-fade-in">
      <header className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-extrabold text-slate-100 flex items-center gap-3 tracking-tight">
            <Bot className="text-cyan-400" /> AI Analyzer Sandbox
          </h2>
          <p className="text-base text-slate-400 mt-2">Submit business requests to the secure Llama 3 analysis engine.</p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-0">
        
        {/* Left Column: Request Input / View */}
        <div className="cyber-panel flex flex-col p-0 overflow-hidden">
          <div className="border-b border-slate-800/40 bg-slate-900/40 p-4 flex justify-between items-center">
            <h3 className="font-semibold text-slate-200">Request Content</h3>
            {isDemo && (
              <button 
                onClick={handleAnalyze}
                disabled={isLoading || !demoInput}
                className="px-5 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold rounded-lg transition-all duration-200 disabled:opacity-50 flex items-center gap-2 clickable"
              >
                {isLoading ? <Loader2 size={16} className="animate-spin" /> : 'Run Analysis'}
              </button>
            )}
          </div>
          <div className="p-4 flex-1 flex flex-col">
            {isDemo ? (
              <textarea 
                value={demoInput}
                onChange={(e) => setDemoInput(e.target.value)}
                className="flex-1 w-full bg-slate-950/20 border border-slate-800 rounded-lg p-4 text-slate-200 focus:outline-none focus:border-cyan-500/50 resize-none font-mono text-sm leading-relaxed"
                placeholder="Paste an email or request here..."
              />
            ) : (
              <div className="flex-1 w-full bg-slate-950/20 border border-slate-800 rounded-lg p-4 text-slate-200 font-mono text-sm whitespace-pre-wrap overflow-auto leading-relaxed">
                {currentData?.content || "Loading..."}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Analysis Results */}
        <div className="cyber-panel flex flex-col overflow-hidden">
          <div className="border-b border-slate-800/40 bg-slate-900/40 p-4">
            <h3 className="font-semibold text-slate-200">AI Trust Analysis</h3>
          </div>
          
          <div className="flex-1 overflow-auto p-6 space-y-8">
            {isLoading ? (
              <div className="h-full flex items-center justify-center">
                <AIAnalysisPipeline />
              </div>
            ) : !currentData?.analysis ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 text-center py-20">
                <Bot size={54} className="mb-4 text-slate-600/80 animate-pulse" />
                <p className="text-base font-semibold text-slate-400">Ready for Analysis</p>
                <p className="text-xs text-slate-500 mt-1.5 max-w-xs">
                  AI will analyze manipulation vectors, check threat intelligence data, and crawl Neo4j relationship maps.
                </p>
              </div>
            ) : (
              <>
                {/* Risk Overview */}
                <div className="flex items-center gap-6 p-4 rounded-xl border border-slate-700/50 bg-slate-800/30">
                  <div className="shrink-0">
                    {getRiskIcon(currentData.analysis.risk_level)}
                  </div>
                  <div>
                    <div className="text-sm text-slate-400 mb-1">Overall Risk Score</div>
                    <div className="flex items-baseline gap-2">
                      <span className={`text-3xl font-bold ${getRiskColor(currentData.analysis.risk_level)}`}>
                        {currentData.analysis.risk_score}
                      </span>
                      <span className="text-slate-500 font-medium">/ 100</span>
                    </div>
                  </div>
                  <div className="ml-auto text-right">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-slate-800 border ${getRiskColor(currentData.analysis.risk_level)} border-current opacity-80`}>
                      {currentData.analysis.risk_level} RISK
                    </span>
                  </div>
                </div>

                {/* Radar Chart */}
                <div>
                  <h4 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Psychology Vectors</h4>
                  <div className="h-[280px] bg-slate-900/30 rounded-xl border border-slate-700/30 p-2">
                    <PsychologyRadar factors={currentData.analysis.psychology} />
                  </div>
                </div>

                {/* Explainability & Flags */}
                <div>
                  <h4 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Explainability Engine</h4>
                  <p className="text-slate-300 text-sm leading-relaxed mb-4 bg-slate-800/50 p-4 rounded-lg border-l-2 border-cyan-500">
                    {currentData.analysis.explanation}
                  </p>
                  
                  {currentData.analysis.flags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {currentData.analysis.flags.map((flag, idx) => (
                        <span key={idx} className="px-3 py-1 bg-red-500/10 border border-red-500/20 text-red-400 rounded-md text-xs flex items-center gap-1">
                          <AlertTriangle size={12} />
                          {flag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default AnalyzerPage;
