import React from 'react';
import { Sparkles, Activity, PlusCircle, Menu } from 'lucide-react';
import type { HealthStatus } from '../types';

interface HeaderProps {
  health: HealthStatus | null;
  healthLoading: boolean;
  onNewResearch: () => void;
  onToggleSidebar: () => void;
  isSidebarOpen: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  healthLoading,
  onNewResearch,
  onToggleSidebar,
  isSidebarOpen,
}) => {
  const isHealthy = health?.status === 'ok' && health?.database === 'connected';

  return (
    <header className="shrink-0 z-30 border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-xl px-3 sm:px-6 py-3 transition-all duration-300">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-2 sm:gap-4">
        {/* Left: Brand & Mobile Sidebar Toggle */}
        <div className="flex items-center gap-2 sm:gap-3 min-w-0">
          <button
            type="button"
            onClick={onToggleSidebar}
            aria-expanded={isSidebarOpen}
            className="md:hidden p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/80 active:bg-slate-800 border border-transparent hover:border-slate-700/60 transition-all duration-200 shrink-0"
            aria-label="Toggle history sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/25 ring-1 ring-white/20 shrink-0 group-hover:scale-105 transition-transform">
              <Sparkles className="w-5 h-5 text-white animate-pulse" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 sm:gap-2">
                <span className="font-extrabold text-sm sm:text-lg text-white tracking-tight truncate">
                  Multi-Agent AI
                </span>
                <span className="text-[10px] sm:text-xs px-2 py-0.5 rounded-full font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shrink-0">
                  Research System
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden lg:block truncate">
                Autonomous Deep Research • LangChain • Gemini • Tavily
              </p>
            </div>
          </div>
        </div>

        {/* Right: Actions & Health Status */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          {/* Mobile Status Indicator */}
          <div
            className={`flex sm:hidden items-center justify-center p-2 rounded-xl border text-xs ${
              healthLoading
                ? 'bg-slate-900 text-amber-400 border-amber-500/30'
                : isHealthy
                ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/50'
                : 'bg-rose-950/60 text-rose-400 border-rose-800/50'
            }`}
            title={`Status: ${isHealthy ? 'Connected' : 'Disconnected'} (API: ${health?.status || 'connecting'}, DB: ${health?.database || 'unknown'})`}
            aria-label="Connection Status"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                healthLoading
                  ? 'bg-amber-400 animate-ping'
                  : isHealthy
                  ? 'bg-emerald-400 animate-pulse'
                  : 'bg-rose-500'
              }`}
            />
          </div>

          {/* Desktop Health status pill */}
          <div
            className={`hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors shadow-sm ${
              healthLoading
                ? 'bg-slate-900 text-slate-400 border-slate-800'
                : isHealthy
                ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/50'
                : 'bg-rose-950/60 text-rose-400 border-rose-800/50'
            }`}
            title={`API: ${health?.status || 'connecting'}, DB: ${health?.database || 'unknown'}`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                healthLoading
                  ? 'bg-amber-400 animate-ping'
                  : isHealthy
                  ? 'bg-emerald-400 animate-pulse'
                  : 'bg-rose-500'
              }`}
            />
            <span className="flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5" />
              {healthLoading
                ? 'Connecting API...'
                : isHealthy
                ? 'Backend & SQLite Ready'
                : 'Backend Disconnected'}
            </span>
            {health?.version && (
              <span className="text-[10px] opacity-75 font-mono ml-0.5">
                v{health.version}
              </span>
            )}
          </div>

          {/* New Research Button */}
          <button
            type="button"
            onClick={onNewResearch}
            className="flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 active:from-indigo-700 text-white shadow-md shadow-indigo-600/25 transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] border border-indigo-400/20"
          >
            <PlusCircle className="w-4 h-4 shrink-0" />
            <span className="whitespace-nowrap">New Research</span>
          </button>
        </div>
      </div>
    </header>
  );
};
