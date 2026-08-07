import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Navbar from './Navbar';

// ===================================
// TrustGuardian AI — App Layout
// Standard shell with sidebar & header
// ===================================

const AppLayout: React.FC = () => {
  return (
    <div className="flex h-screen bg-[#0a0e1a] text-slate-100 overflow-hidden">
      <Sidebar />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Navbar />

        {/* Page Content */}
        <div className="flex-1 overflow-auto p-6 bg-grid">
          <div className="w-full h-full">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
};

export default AppLayout;
