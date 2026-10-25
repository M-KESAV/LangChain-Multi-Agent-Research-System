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
}) => {
  const isHealthy = health?.status === 'ok' && health?.database === 'connected';

  return (
    <header className="sticky top-0 z-30 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-4 sm:px-6 py-3.5 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Left: Brand */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onToggleSidebar}
            className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Toggle history sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 ring-1 ring-white/20">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base sm:text-lg text-white tracking-tight">
                  Multi-Agent AI
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  Research System
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Autonomous Deep Research • LangChain • Gemini • Tavily
              </p>
            </div>
          </div>
        </div>

        {/* Right: Actions & Health Status */}
        <div className="flex items-center gap-3">
          {/* Health status pill */}
          <div
            className={`hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
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
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white shadow-md shadow-indigo-600/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Research</span>
          </button>
        </div>
      </div>
    </header>
  );
};
