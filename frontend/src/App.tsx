import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import ProtectedRoute from './components/layout/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import AnalyzerPage from './pages/AnalyzerPage';
import GraphPage from './pages/GraphPage';
import RequestsPage from './pages/RequestsPage';
import SandboxPage from './pages/SandboxPage';
import ExplainablePage from './pages/ExplainablePage';
import ReplayPage from './pages/ReplayPage';
import SettingsPage from './pages/SettingsPage';
import { useAuthStore } from './store/authStore';

// ===================================
// TrustGuardian AI — App Router
// ===================================

const App: React.FC = () => {
  const { isAuthenticated, isLoading, initialize } = useAuthStore();

  useEffect(() => {
    initialize();
  }, [initialize]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0a0e1a]">
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-slate-700 border-t-cyan-500 rounded-full animate-spin mb-4"></div>
          <p className="text-slate-400 font-medium">Initializing TrustGuardian...</p>
        </div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route 
          path="/login" 
          element={!isAuthenticated ? <LoginPage /> : <Navigate to="/dashboard" replace />} 
        />

        {/* Protected Routes */}
        <Route path="/" element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="analyzer/:id?" element={<AnalyzerPage />} />
            <Route path="graph" element={<GraphPage />} />
            <Route path="requests" element={<RequestsPage />} />
            <Route path="sandbox" element={<SandboxPage />} />
            <Route path="explainable" element={<ExplainablePage />} />
            <Route path="replay" element={<ReplayPage />} />
            <Route path="settings" element={<SettingsPage />} />
            
            {/* Catch-all for other Module placeholders */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
