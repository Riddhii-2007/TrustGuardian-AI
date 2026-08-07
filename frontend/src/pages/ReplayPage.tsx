import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, FastForward, Terminal, Layers } from 'lucide-react';

// ==========================================
// TrustGuardian AI — Trust Replay Player
// Simulates scrolling real-time log playback
// ==========================================

interface LogEvent {
  time: string;
  source: string;
  message: string;
  level: 'info' | 'warn' | 'error';
}

const ReplayPage: React.FC = () => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [progress, setProgress] = useState<number>(0);
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const logTerminalRef = useRef<HTMLDivElement>(null);

  // Playback timer
  useEffect(() => {
    let timer: any;
    if (isPlaying) {
      timer = setInterval(() => {
        setProgress(prev => {
          if (prev >= 100) {
            setIsPlaying(false);
            return 100;
          }
          // Append mock logs as progress increases
          addMockLog(prev);
          return prev + (1 * playbackSpeed);
        });
      }, 500);
    }
    return () => clearInterval(timer);
  }, [isPlaying, playbackSpeed]);

  // Auto-scroll logs terminal
  useEffect(() => {
    if (logTerminalRef.current) {
      logTerminalRef.current.scrollTop = logTerminalRef.current.scrollHeight;
    }
  }, [logs]);

  const addMockLog = (prog: number) => {
    const timestamp = new Date().toLocaleTimeString();
    const mockEvents: LogEvent[] = [
      { time: timestamp, source: 'PORTAL_INGEST', message: 'Intercepting new incoming Gmail envelope headers...', level: 'info' },
      { time: timestamp, source: 'PII_SHIELD', message: 'Analyzing body context for sensitive routing numbers...', level: 'info' },
      { time: timestamp, source: 'DNS_INTEGRITY', message: 'Resolving domain signature SPF, DKIM hashes...', level: 'info' },
      { time: timestamp, source: 'BEC_DETECTION', message: 'WARNING: Pattern match threshold exceed on Urgency vectors.', level: 'warn' },
      { time: timestamp, source: 'TRUST_SCORE', message: 'Re-evaluating Trust Score: final result 52.0 (RISK_DETECTED).', level: 'error' }
    ];

    // Pick one based on progress
    const idx = Math.floor(prog / 20) % mockEvents.length;
    setLogs(prev => [...prev, mockEvents[idx]]);
  };

  const handlePlayToggle = () => {
    if (progress >= 100) {
      setProgress(0);
      setLogs([]);
    }
    setIsPlaying(!isPlaying);
  };

  const handleSpeedToggle = () => {
    setPlaybackSpeed(prev => (prev === 1 ? 2 : prev === 2 ? 4 : 1));
  };

  return (
    <div className="space-y-8 animate-fade-in pb-8">
      <header>
        <h2 className="text-3xl font-extrabold text-slate-100 flex items-center gap-3 tracking-tight">
          <Terminal className="text-cyan-400" /> Security Audit Trust Replay
        </h2>
        <p className="text-base text-slate-400 mt-2">Replay historical email scan sessions and view telemetry event streams.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Playback Controls & Progress Panel */}
        <div className="cyber-panel space-y-6 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-200 border-b border-slate-800/40 pb-3 flex items-center gap-2">
              <Layers size={18} className="text-cyan-400" />
              Auditor Controller
            </h3>

            {/* Progress bar */}
            <div className="mt-8 space-y-2">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-400">Scan Session Playback Progress</span>
                <span className="text-cyan-400">{Math.min(100, Math.floor(progress))}%</span>
              </div>
              <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300 shadow-[0_0_10px_rgba(6,182,212,0.3)]" 
                  style={{ width: `${progress}%` }} 
                />
              </div>
            </div>

            {/* Timeline state */}
            <div className="mt-6 grid grid-cols-2 gap-4">
              <div className="bg-slate-950/40 border border-slate-900 rounded-xl p-3.5 text-center">
                <div className="text-xs text-slate-500 font-bold uppercase tracking-wider">Status</div>
                <div className="text-base font-extrabold text-slate-200 mt-1">
                  {isPlaying ? 'Replaying' : progress >= 100 ? 'Completed' : 'Paused'}
                </div>
              </div>
              <div className="bg-slate-950/40 border border-slate-900 rounded-xl p-3.5 text-center">
                <div className="text-xs text-slate-500 font-bold uppercase tracking-wider">Speed</div>
                <div className="text-base font-extrabold text-cyan-400 mt-1">{playbackSpeed}x Normal</div>
              </div>
            </div>
          </div>

          <div className="flex space-x-3 pt-4">
            <button 
              onClick={handlePlayToggle}
              className="flex-1 py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all duration-200 shadow-glow-sm clickable"
            >
              {isPlaying ? <Pause size={16} /> : <Play size={16} />}
              {isPlaying ? 'Pause Replay' : 'Start Playback'}
            </button>
            <button 
              onClick={handleSpeedToggle}
              className="px-4 py-3 bg-slate-900/60 hover:bg-slate-800/80 text-slate-300 rounded-xl border border-slate-800 transition-all duration-200 text-sm font-semibold flex items-center justify-center gap-1.5 clickable"
            >
              <FastForward size={16} />
              {playbackSpeed}x
            </button>
          </div>
        </div>

        {/* Emitters terminal window */}
        <div className="lg:col-span-2 cyber-panel flex flex-col h-[400px]">
          <div className="flex justify-between items-center border-b border-slate-800/40 pb-3">
            <h3 className="text-base font-bold text-slate-200 flex items-center gap-2">
              <Terminal size={16} className="text-cyan-400" />
              Live Telemetry Console
            </h3>
            <span className="text-[10px] font-mono text-slate-500">60 FPS SECURE EVENT STREAM</span>
          </div>

          {/* Logs terminal box */}
          <div 
            ref={logTerminalRef}
            className="flex-1 min-h-0 bg-slate-950/60 rounded-xl border border-slate-900/80 p-4 mt-4 font-mono text-xs overflow-y-auto space-y-3 scrollbar-thin select-text"
          >
            {logs.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-600">
                &gt;_ Click play to stream session logs...
              </div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="flex items-start space-x-2">
                  <span className="text-slate-600">[{log.time}]</span>
                  <span className={`font-bold ${
                    log.level === 'error' ? 'text-red-400' : log.level === 'warn' ? 'text-yellow-400' : 'text-cyan-400'
                  }`}>
                    {log.source}:
                  </span>
                  <span className="text-slate-300 flex-1">{log.message}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReplayPage;
