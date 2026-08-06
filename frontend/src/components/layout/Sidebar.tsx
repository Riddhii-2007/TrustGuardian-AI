import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Mail, Network, PlaySquare, History, ShieldAlert, Bot, Settings } from 'lucide-react';

// ===================================
// TrustGuardian AI — Sidebar
// ===================================

const Sidebar: React.FC = () => {
  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
    { name: 'AI Analyzer', path: '/analyzer', icon: <Bot size={20} /> },
    { name: 'Business Requests', path: '/requests', icon: <Mail size={20} /> },
    { name: 'Knowledge Graph', path: '/graph', icon: <Network size={20} /> },
    { name: 'Decision Sandbox', path: '/sandbox', icon: <PlaySquare size={20} /> },
    { name: 'Trust Replay', path: '/replay', icon: <History size={20} /> },
    { name: 'Explainable AI', path: '/explainable', icon: <ShieldAlert size={20} /> },
    { name: 'Settings', path: '/settings', icon: <Settings size={20} /> },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-[#0f1629] p-4 flex flex-col h-full">
      <div className="flex items-center space-x-3 mb-8 px-2">
        <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center glow-border">
          <span className="text-xl text-cyan-400">🛡️</span>
        </div>
        <div className="text-lg font-bold gradient-text tracking-wider">
          TrustGuardian
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto pr-2">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 px-3">
          Platform Modules
        </div>
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                isActive
                  ? 'bg-slate-800/80 text-cyan-400 border border-slate-700/50 shadow-glow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
              }`
            }
          >
            {item.icon}
            <span className="font-medium">{item.name}</span>
          </NavLink>
        ))}
      </nav>

      <div className="mt-4 p-4 rounded-xl bg-slate-800/30 border border-slate-700/50">
        <div className="text-xs text-slate-400 mb-2">System Status</div>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-green-500 pulse-dot"></div>
          <span className="text-sm font-medium text-slate-300">All Systems Operational</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
