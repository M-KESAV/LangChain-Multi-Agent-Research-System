import React, { useState, useMemo } from 'react';
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
  Calendar,
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

interface GroupedHistory {
  period: string;
  items: ResearchSummary[];
}

function groupHistoryByPeriod(items: ResearchSummary[]): GroupedHistory[] {
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const startOfYesterday = startOfToday - 86400000;
  const startOf7Days = startOfToday - 6 * 86400000;
  const startOf30Days = startOfToday - 29 * 86400000;

  const buckets: Record<string, ResearchSummary[]> = {
    Today: [],
    Yesterday: [],
    'Previous 7 Days': [],
    'Previous 30 Days': [],
    Older: [],
  };

  for (const item of items) {
    try {
      const itemTime = new Date(item.created_at).getTime();
      if (isNaN(itemTime)) {
        buckets['Older'].push(item);
      } else if (itemTime >= startOfToday) {
        buckets['Today'].push(item);
      } else if (itemTime >= startOfYesterday) {
        buckets['Yesterday'].push(item);
      } else if (itemTime >= startOf7Days) {
        buckets['Previous 7 Days'].push(item);
      } else if (itemTime >= startOf30Days) {
        buckets['Previous 30 Days'].push(item);
      } else {
        buckets['Older'].push(item);
      }
    } catch {
      buckets['Older'].push(item);
    }
  }

  const order = ['Today', 'Yesterday', 'Previous 7 Days', 'Previous 30 Days', 'Older'];
  const groups: GroupedHistory[] = [];
  for (const period of order) {
    if (buckets[period].length > 0) {
      groups.push({ period, items: buckets[period] });
    }
  }
  return groups;
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

  const filteredHistory = useMemo(() => {
    if (!searchTerm.trim()) return history;
    const term = searchTerm.toLowerCase();
    return history.filter((item) =>
      item.topic.toLowerCase().includes(term)
    );
  }, [history, searchTerm]);

  // Group history into standard temporal periods: Today, Yesterday, Previous 7 Days, Older
  const groupedHistory = useMemo(() => {
    return groupHistoryByPeriod(filteredHistory);
  }, [filteredHistory]);

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

  const renderHistoryItem = (item: ResearchSummary) => {
    const isSelected = selectedId === item.id;
    const isDeleting = deleteConfirmId === item.id;

    return (
      <div
        key={item.id}
        className={`group relative rounded-xl border p-3 transition-all duration-200 ${
          isSelected
            ? 'bg-indigo-950/40 border-indigo-500/60 shadow-md shadow-indigo-500/10 ring-1 ring-indigo-500/20'
            : 'bg-slate-950/40 border-slate-800/60 hover:bg-slate-850 hover:border-slate-700/80 hover:shadow-sm'
        }`}
      >
        {/* Active Indicator Bar */}
        {isSelected && (
          <div className="absolute left-0 top-2.5 bottom-2.5 w-1 bg-gradient-to-b from-indigo-500 to-cyan-400 rounded-r-full" />
        )}

        {/* Item Content Button */}
        <button
          type="button"
          onClick={() => onSelectRun(item.id)}
          className="w-full text-left focus:outline-none"
        >
          <div className="flex items-start justify-between gap-2 mb-1.5 pl-1">
            {renderStatusBadge(item.status)}
            <span className="text-[10px] text-slate-500 font-mono">
              {formatDate(item.created_at)}
            </span>
          </div>

          <h4 className="text-xs font-semibold text-slate-200 line-clamp-2 leading-relaxed group-hover:text-white transition-colors pl-1">
            {item.topic}
          </h4>
        </button>

        {/* Actions / Delete */}
        <div className="mt-2.5 pt-2 border-t border-slate-800/50 flex items-center justify-between text-[11px] pl-1">
          <button
            type="button"
            onClick={() => onSelectRun(item.id)}
            className="text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1 transition-colors"
          >
            View Report
            <ChevronRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
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
                className="px-2 py-0.5 rounded text-[10px] bg-rose-600 text-white font-medium hover:bg-rose-500 transition-colors"
              >
                Yes
              </button>
              <button
                type="button"
                onClick={() => setDeleteConfirmId(null)}
                className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors"
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
              className="text-slate-400 hover:text-rose-400 p-1.5 rounded-lg transition-colors opacity-70 hover:opacity-100 sm:opacity-0 sm:group-hover:opacity-100 focus:opacity-100"
              title="Delete run"
              aria-label="Delete run"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Mobile overlay with blur */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-40 md:hidden transition-opacity duration-300"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar container - rigidly bounded in flex layout */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 h-full min-h-0 w-[85vw] max-w-xs sm:w-80 md:w-80 lg:w-88 shrink-0 bg-slate-900/95 md:bg-slate-900/70 border-r border-slate-800/80 backdrop-blur-xl flex flex-col transition-transform duration-300 ease-in-out shadow-2xl md:shadow-none overflow-hidden ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between gap-2 shrink-0">
          <div className="flex items-center gap-2 text-slate-200">
            <History className="w-5 h-5 text-indigo-400" />
            <span className="font-semibold text-sm">Research History</span>
            <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full font-mono font-medium">
              {history.length}
            </span>
          </div>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={onRefreshHistory}
              disabled={loading}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-50"
              title="Refresh history"
              aria-label="Refresh history"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
            </button>
            <button
              type="button"
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg md:hidden transition-colors"
              aria-label="Close sidebar"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Search Filter */}
        <div className="p-3 border-b border-slate-800/60 shrink-0">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search past research..."
              className="w-full bg-slate-950/70 border border-slate-800/90 rounded-lg pl-9 pr-8 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm('')}
                className="absolute right-2.5 top-2.5 text-slate-500 hover:text-slate-300 p-0.5 rounded"
                title="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* History Item List - Independent smooth scrolling */}
        <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain p-2 space-y-4">
          {loading && history.length === 0 ? (
            <div className="py-12 text-center text-slate-500 space-y-2">
              <Loader2 className="w-6 h-6 animate-spin mx-auto text-indigo-400" />
              <p className="text-xs font-medium">Loading research history...</p>
            </div>
          ) : filteredHistory.length === 0 ? (
            <div className="py-12 text-center text-slate-500 px-4">
              <FileText className="w-8 h-8 mx-auto text-slate-600 mb-2 opacity-60" />
              <p className="text-xs font-semibold text-slate-400">No research runs found</p>
              {searchTerm ? (
                <p className="text-[11px] text-slate-500 mt-1">No matching topics for "{searchTerm}"</p>
              ) : (
                <p className="text-[11px] text-slate-500 mt-1">Start your first autonomous research run above</p>
              )}
            </div>
          ) : searchTerm ? (
            /* Search Results View */
            <div className="space-y-2">
              <div className="flex items-center justify-between px-2 pt-1 pb-1">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                  Search Results
                </span>
                <span className="text-[10px] font-mono text-indigo-400 bg-indigo-950/60 border border-indigo-800/40 px-2 py-0.5 rounded-full">
                  {filteredHistory.length} found
                </span>
              </div>
              {filteredHistory.map(renderHistoryItem)}
            </div>
          ) : (
            /* Grouped View by Time Period */
            groupedHistory.map((group) => (
              <div key={group.period} className="space-y-2">
                <div className="flex items-center justify-between px-2 pt-1 pb-0.5 text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3 h-3 text-slate-500" />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      {group.period}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 bg-slate-800/80 px-1.5 py-0.2 rounded-full">
                    {group.items.length}
                  </span>
                </div>
                <div className="space-y-2">
                  {group.items.map(renderHistoryItem)}
                </div>
              </div>
            ))
          )}
        </div>
      </aside>
    </>
  );
};
