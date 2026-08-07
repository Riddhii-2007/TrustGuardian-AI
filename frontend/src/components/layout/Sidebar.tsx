import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Mail, Network, PlaySquare, History, ShieldAlert, Bot, Settings } from 'lucide-react';

// ===================================
// TrustGuardian AI — Sidebar
// ===================================

const Sidebar: React.FC = () => {
  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={22} /> },
    { name: 'AI Analyzer', path: '/analyzer', icon: <Bot size={22} /> },
    { name: 'Business Requests', path: '/requests', icon: <Mail size={22} /> },
    { name: 'Knowledge Graph', path: '/graph', icon: <Network size={22} /> },
    { name: 'Decision Sandbox', path: '/sandbox', icon: <PlaySquare size={22} /> },
    { name: 'Trust Replay', path: '/replay', icon: <History size={22} /> },
    { name: 'Explainable AI', path: '/explainable', icon: <ShieldAlert size={22} /> },
    { name: 'Settings', path: '/settings', icon: <Settings size={22} /> },
  ];

  return (
    <aside className="w-72 border-r border-slate-800 bg-[#0f1629] p-6 flex flex-col h-full">
      <div className="flex items-center space-x-3 mb-10 px-2">
        <div className="w-10 h-10 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center glow-border">
          <span className="text-2xl text-cyan-400">🛡️</span>
        </div>
        <div className="text-xl font-bold gradient-text tracking-wider">
          TrustGuardian
        </div>
      </div>

      <nav className="flex-1 space-y-2 overflow-y-auto pr-2">
        <div className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4 px-3">
          Platform Modules
        </div>
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center space-x-4 px-4 py-3.5 rounded-xl transition-all duration-200 ${
                isActive
                  ? 'bg-slate-800/80 text-cyan-400 border border-slate-700/50 shadow-glow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
              }`
            }
          >
            {item.icon}
            <span className="font-semibold text-base">{item.name}</span>
          </NavLink>
        ))}
      </nav>

      <div className="mt-6 p-5 rounded-2xl bg-slate-800/30 border border-slate-700/50">
        <div className="text-xs text-slate-400 mb-2">System Status</div>
        <div className="flex items-center space-x-2">
          <div className="w-2.5 h-2.5 rounded-full bg-green-500 pulse-dot"></div>
          <span className="text-base font-semibold text-slate-300">All Systems Operational</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
