import React, { useState } from 'react';
import { Settings, Shield, Cpu, Save, RefreshCw } from 'lucide-react';

// ==========================================
// TrustGuardian AI — Settings Console
// Manages LLM endpoints, temperature, and database connections
// ==========================================

const SettingsPage: React.FC = () => {
  const [provider, setProvider] = useState<string>('gemini');
  const [temperature, setTemperature] = useState<number>(0.1);
  const [piiFilter, setPiiFilter] = useState<boolean>(true);
  const [threatIntel, setThreatIntel] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      alert('Settings updated successfully!');
    }, 1000);
  };

  return (
    <div className="space-y-8 animate-fade-in pb-8">
      <header>
        <h2 className="text-3xl font-extrabold text-slate-100 flex items-center gap-3 tracking-tight">
          <Settings className="text-cyan-400" /> Platform Configuration
        </h2>
        <p className="text-base text-slate-400 mt-2">Manage LLM routers, scanning rules, and database credentials.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LLM & Temperature configuration */}
        <div className="cyber-panel space-y-6">
          <h3 className="text-lg font-bold text-slate-200 border-b border-slate-800/40 pb-3 flex items-center gap-2">
            <Cpu size={18} className="text-cyan-400" />
            AI Language Engine Settings
          </h3>

          <div className="space-y-4">
            {/* Engine Selection */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400">Primary Inference Provider</label>
              <select 
                value={provider} 
                onChange={(e) => setProvider(e.target.value)}
                className="w-full bg-slate-950 border border-slate-900 focus:border-cyan-500 rounded-xl px-4 py-3 text-sm font-semibold text-slate-200 focus:outline-none"
              >
                <option value="gemini">Google Gemini (Default)</option>
                <option value="groq">Groq Llama 3</option>
                <option value="openrouter">OpenRouter Multi-Gateway</option>
              </select>
            </div>

            {/* Temperature Slider */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-400">Model Temperature</span>
                <span className="text-cyan-400">{temperature}</span>
              </div>
              <input 
                type="range" 
                min="0.0" 
                max="1.0" 
                step="0.1"
                value={temperature} 
                onChange={(e) => setTemperature(Number(e.target.value))}
                className="w-full h-1 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-cyan-500"
              />
            </div>
          </div>
        </div>

        {/* Threat policies & compliance filters */}
        <div className="cyber-panel space-y-6 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-200 border-b border-slate-800/40 pb-3 flex items-center gap-2">
              <Shield size={18} className="text-cyan-400" />
              Policy Filters & Compliance Shield
            </h3>

            <div className="space-y-4 mt-6">
              {/* Toggle 1 */}
              <div className="flex justify-between items-center p-3.5 bg-slate-950/40 border border-slate-900 rounded-xl">
                <div>
                  <div className="text-xs font-bold text-slate-300">PII Shield Redactor</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Mask Aadhaar, PAN and banking routing strings.</div>
                </div>
                <input 
                  type="checkbox" 
                  checked={piiFilter} 
                  onChange={(e) => setPiiFilter(e.target.checked)}
                  className="w-4 h-4 rounded text-cyan-600 bg-slate-900 border-slate-800 focus:ring-cyan-500"
                />
              </div>

              {/* Toggle 2 */}
              <div className="flex justify-between items-center p-3.5 bg-slate-950/40 border border-slate-900 rounded-xl">
                <div>
                  <div className="text-xs font-bold text-slate-300">VirusTotal Domain Reputation</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Cross-reference unknown URLs with threat intelligence databases.</div>
                </div>
                <input 
                  type="checkbox" 
                  checked={threatIntel} 
                  onChange={(e) => setThreatIntel(e.target.checked)}
                  className="w-4 h-4 rounded text-cyan-600 bg-slate-900 border-slate-800 focus:ring-cyan-500"
                />
              </div>
            </div>
          </div>

          <button 
            onClick={handleSave}
            disabled={isSaving}
            className="w-full py-3 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-800/40 text-white disabled:text-slate-600 border border-transparent disabled:border-slate-800 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all duration-200 shadow-glow-sm clickable mt-8"
          >
            {isSaving ? <RefreshCw className="animate-spin" size={16} /> : <Save size={16} />}
            {isSaving ? 'Saving Configurations...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
