import React, { useState } from 'react';
import {
  History,
  Trash2,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ChevronRight,
  X,
  FileText,
} from 'lucide-react';
import type { ResearchSummary } from '../types';

interface SidebarProps {
  history: ResearchSummary[];
  loading: boolean;
  selectedId: string | null;
  onSelectRun: (id: string) => void;
  onDeleteRun: (id: string) => void;
  onRefreshHistory: () => void;
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  history,
  loading,
  selectedId,
  onSelectRun,
  onDeleteRun,
  onRefreshHistory,
  isOpen,
  onClose,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const filteredHistory = history.filter((item) =>
    item.topic.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  const renderStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2 py-0.5 rounded-md">
            <CheckCircle2 className="w-3 h-3" />
            Done
          </span>
        );
      case 'running':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-cyan-400 bg-cyan-950/60 border border-cyan-800/40 px-2 py-0.5 rounded-md animate-pulse">
            <Loader2 className="w-3 h-3 animate-spin" />
            Running
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-rose-400 bg-rose-950/60 border border-rose-800/40 px-2 py-0.5 rounded-md">
            <AlertCircle className="w-3 h-3" />
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center text-[11px] font-medium text-slate-400 bg-slate-800 px-2 py-0.5 rounded-md">
            {status}
          </span>
        );
    }
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 w-80 sm:w-88 bg-slate-900/95 md:bg-slate-900/60 border-r border-slate-800 flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-slate-200">
            <History className="w-5 h-5 text-indigo-400" />
            <span className="font-semibold text-sm">Research History</span>
            <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full font-mono">
              {history.length}
            </span>
          </div>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={onRefreshHistory}
              disabled={loading}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-50"
              title="Refresh history"
              aria-label="Refresh history"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg md:hidden transition-colors"
              aria-label="Close sidebar"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Search Filter */}
        <div className="p-3 border-b border-slate-800/60">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search past research..."
              className="w-full bg-slate-950/70 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
            />
          </div>
        </div>

        {/* History Item List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
          {loading && history.length === 0 ? (
            <div className="p-6 text-center text-slate-500 space-y-2">
              <Loader2 className="w-6 h-6 animate-spin mx-auto text-indigo-400" />
              <p className="text-xs">Loading research history...</p>
            </div>
          ) : filteredHistory.length === 0 ? (
            <div className="p-6 text-center text-slate-500">
              <FileText className="w-8 h-8 mx-auto text-slate-600 mb-2 opacity-50" />
              <p className="text-xs font-medium">No research runs found</p>
              {searchTerm && (
                <p className="text-[11px] text-slate-600 mt-1">Try a different search term</p>
              )}
            </div>
          ) : (
            filteredHistory.map((item) => {
              const isSelected = selectedId === item.id;
              const isDeleting = deleteConfirmId === item.id;

              return (
                <div
                  key={item.id}
                  className={`group relative rounded-xl border p-3 transition-all ${
                    isSelected
                      ? 'bg-indigo-950/40 border-indigo-500/50 shadow-sm shadow-indigo-500/10'
                      : 'bg-slate-950/40 border-slate-800/60 hover:bg-slate-800/50 hover:border-slate-700'
                  }`}
                >
                  {/* Item Content Button */}
                  <button
                    type="button"
                    onClick={() => onSelectRun(item.id)}
                    className="w-full text-left focus:outline-none"
                  >
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      {renderStatusBadge(item.status)}
                      <span className="text-[10px] text-slate-500 font-mono">
                        {formatDate(item.created_at)}
                      </span>
                    </div>

                    <h4 className="text-xs font-semibold text-slate-200 line-clamp-2 leading-relaxed group-hover:text-white transition-colors">
                      {item.topic}
                    </h4>
                  </button>

                  {/* Actions / Delete */}
                  <div className="mt-2.5 pt-2 border-t border-slate-800/40 flex items-center justify-between text-[11px]">
                    <button
                      type="button"
                      onClick={() => onSelectRun(item.id)}
                      className="text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1 transition-colors"
                    >
                      View Report
                      <ChevronRight className="w-3 h-3" />
                    </button>

                    {isDeleting ? (
                      <div className="flex items-center gap-1.5 animate-fadeIn">
                        <span className="text-[10px] text-rose-400 font-semibold">Delete?</span>
                        <button
                          type="button"
                          onClick={() => {
                            onDeleteRun(item.id);
                            setDeleteConfirmId(null);
                          }}
                          className="px-1.5 py-0.5 rounded text-[10px] bg-rose-600 text-white font-medium hover:bg-rose-500"
                        >
                          Yes
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeleteConfirmId(null)}
                          className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 hover:bg-slate-700"
                        >
                          No
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeleteConfirmId(item.id);
                        }}
                        className="text-slate-500 hover:text-rose-400 p-1 rounded transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                        title="Delete run"
                        aria-label="Delete run"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </aside>
    </>
  );
};
