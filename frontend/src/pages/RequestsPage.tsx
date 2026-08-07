import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { requestsApi } from '../api/requests.api';
import { Mail, ShieldCheck, ShieldAlert, AlertTriangle, AlertCircle, Eye, Loader2 } from 'lucide-react';

// ==========================================
// TrustGuardian AI — Business Requests Ledger
// Lists all ingested requests and maps actions to sandbox scanning
// ==========================================

const RequestsPage: React.FC = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['requestsList'],
    queryFn: requestsApi.getRequests
  });

  const getRiskBadge = (level: string | undefined) => {
    const lvl = level?.toLowerCase() || 'unknown';
    let colors = 'bg-slate-800/40 border-slate-700/50 text-slate-400';
    let icon = <AlertCircle size={14} />;

    if (lvl === 'critical') {
      colors = 'bg-red-500/10 border-red-500/20 text-red-400';
      icon = <ShieldAlert size={14} />;
    } else if (lvl === 'high') {
      colors = 'bg-orange-500/10 border-orange-500/20 text-orange-400';
      icon = <AlertTriangle size={14} />;
    } else if (lvl === 'medium' || lvl === 'low') {
      colors = 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400';
      icon = <AlertCircle size={14} />;
    } else if (lvl === 'safe') {
      colors = 'bg-green-500/10 border-green-500/20 text-green-400';
      icon = <ShieldCheck size={14} />;
    }

    return (
      <span className={`px-2.5 py-1 rounded-md text-xs font-bold uppercase border flex items-center gap-1.5 w-fit ${colors}`}>
        {icon}
        {level || 'Pending'}
      </span>
    );
  };

  const getRiskColor = (score: number | undefined) => {
    if (score === undefined) return 'text-slate-500';
    if (score > 80) return 'text-red-400';
    if (score > 50) return 'text-yellow-400';
    return 'text-cyan-400';
  };

  return (
    <div className="h-full flex flex-col space-y-6 animate-fade-in pb-8">
      <header>
        <h2 className="text-3xl font-extrabold text-slate-100 flex items-center gap-3 tracking-tight">
          <Mail className="text-cyan-400" /> Ingested Communication Logs
        </h2>
        <p className="text-base text-slate-400 mt-2">Active inspection list of company requests, invoices, and Gmail items.</p>
      </header>

      <div className="flex-1 min-h-0 cyber-panel p-0 overflow-hidden flex flex-col relative">
        {isLoading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/40">
            <Loader2 className="animate-spin text-cyan-500 mb-4" size={48} />
            <p className="text-slate-400 font-semibold">Querying Ingested Logs database...</p>
          </div>
        ) : error ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/40 p-8 text-center">
            <div className="text-red-400 text-xl font-bold mb-2">Connection Error</div>
            <p className="text-slate-400 max-w-md">Failed to fetch logs from FastAPI backend.</p>
          </div>
        ) : (
          <div className="flex-1 overflow-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800/60 bg-slate-950/20 text-[10px] font-bold text-slate-500 uppercase tracking-widest sticky top-0 backdrop-blur-md z-10">
                  <th className="py-4 px-6">Requester</th>
                  <th className="py-4 px-6">Subject / Title</th>
                  <th className="py-4 px-6">Risk Classification</th>
                  <th className="py-4 px-6 text-center">Risk Score</th>
                  <th className="py-4 px-6">Received</th>
                  <th className="py-4 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {data?.items.map((req) => (
                  <tr key={req.id} className="hover:bg-slate-900/10 transition-colors group">
                    <td className="py-4 px-6 font-mono text-xs text-slate-300 font-semibold">{req.requester}</td>
                    <td className="py-4 px-6 max-w-xs truncate">
                      <div className="text-sm font-semibold text-slate-200">{req.title}</div>
                      <div className="text-xs text-slate-500 mt-0.5 truncate">{req.content}</div>
                    </td>
                    <td className="py-4 px-6">{getRiskBadge(req.analysis?.risk_level)}</td>
                    <td className="py-4 px-6 text-center font-mono font-bold text-sm">
                      <span className={getRiskColor(req.analysis?.risk_score)}>
                        {req.analysis?.risk_score !== undefined ? `${req.analysis.risk_score}` : '--'}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-xs text-slate-400 font-semibold">
                      {new Date(req.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-4 px-6 text-right">
                      <Link 
                        to={`/analyzer/${req.id}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-900/60 hover:bg-cyan-900/30 hover:text-cyan-400 border border-slate-800 hover:border-cyan-500/30 rounded-lg text-xs font-bold text-slate-300 transition-all duration-200 clickable"
                      >
                        <Eye size={13} />
                        Investigate
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default RequestsPage;
