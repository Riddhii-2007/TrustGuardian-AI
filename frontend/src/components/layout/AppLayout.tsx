import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import { CyberGridBackground } from '../common/CyberGridBackground';
import { CustomCursor } from '../common/CustomCursor';

// ===================================
// TrustGuardian AI — App Layout
// Standard shell with sidebar & header
// ===================================

const AppLayout: React.FC = () => {
  return (
    <div className="flex h-screen bg-[#050816] text-slate-100 overflow-hidden relative">
      {/* Premium Ambient Background and Custom Cursor */}
      <CyberGridBackground />
      <CustomCursor />

      <Sidebar />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative z-10">
        <Navbar />

        {/* Page Content */}
        <div className="flex-1 overflow-auto p-8">
          <div className="w-full h-full">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
};

export default AppLayout;
