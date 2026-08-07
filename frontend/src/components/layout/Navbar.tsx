import React, { useState } from 'react';
import { useAuthStore } from '../../store/authStore';
import { Bell, Search, LogOut, User, Settings } from 'lucide-react';

// ===================================
// TrustGuardian AI — Navbar
// ===================================

const Navbar: React.FC = () => {
  const { user, signOut } = useAuthStore();
  const [showDropdown, setShowDropdown] = useState(false);

  return (
    <header className="h-20 border-b border-slate-800 bg-[#0f1629]/80 flex items-center justify-between px-8 backdrop-blur-md z-20 sticky top-0">
      
      {/* Left: Global Search (Placeholder) */}
      <div className="flex-1 max-w-md relative hidden md:block">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search size={22} className="text-slate-500" />
        </div>
        <input
          type="text"
          className="block w-full pl-10 pr-3 py-2 border border-slate-700 rounded-lg leading-5 bg-slate-900/50 text-slate-300 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 sm:text-base transition-colors"
          placeholder="Search entities, domains, or requests..."
        />
      </div>

      {/* Right: Actions & Profile */}
      <div className="flex items-center space-x-4 ml-auto">
        
        {/* Notifications */}
        <button className="p-2 text-slate-400 hover:text-slate-200 transition-colors relative">
          <Bell size={22} />
          <span className="absolute top-1 right-1 block h-2 w-2 rounded-full bg-red-500 ring-2 ring-[#0f1629]"></span>
        </button>

        <div className="w-px h-6 bg-slate-700 mx-2"></div>

        {/* User Profile Dropdown */}
        <div className="relative">
          <button 
            onClick={() => setShowDropdown(!showDropdown)}
            className="flex items-center space-x-3 focus:outline-none group"
          >
            <div className="text-right hidden sm:block">
              <div className="text-base font-semibold text-slate-200">{user?.full_name}</div>
              <div className="text-sm text-slate-500 capitalize">{user?.role}</div>
            </div>
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="Profile" className="h-11 w-11 rounded-full border border-slate-600 group-hover:border-cyan-400 transition-colors" />
            ) : (
              <div className="h-11 w-11 rounded-full bg-slate-700 border border-slate-600 flex items-center justify-center group-hover:border-cyan-400 transition-colors">
                <span className="text-base font-medium text-slate-300">
                  {user?.full_name?.charAt(0) || 'U'}
                </span>
              </div>
            )}
          </button>

          {/* Dropdown Menu */}
          {showDropdown && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowDropdown(false)}></div>
              <div className="absolute right-0 mt-2 w-48 rounded-xl shadow-card-hover bg-[#151d35] border border-slate-700 py-1 z-20 animate-fade-in origin-top-right">
                <div className="px-4 py-3 border-b border-slate-700/50 sm:hidden">
                  <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
                  <p className="text-xs text-slate-400 truncate">{user?.email}</p>
                </div>
                
                <button className="w-full text-left px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white flex items-center space-x-2 transition-colors">
                  <User size={16} />
                  <span>Profile</span>
                </button>
                <button className="w-full text-left px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white flex items-center space-x-2 transition-colors">
                  <Settings size={16} />
                  <span>Settings</span>
                </button>
                
                <div className="my-1 border-t border-slate-700/50"></div>
                
                <button 
                  onClick={() => {
                    setShowDropdown(false);
                    signOut();
                  }}
                  className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 hover:text-red-300 flex items-center space-x-2 transition-colors"
                >
                  <LogOut size={16} />
                  <span>Sign out</span>
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
