import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ResearchForm } from './components/ResearchForm';
import { ProgressTimeline } from './components/ProgressTimeline';
import { ReportViewer } from './components/ReportViewer';
import { EmptyState } from './components/EmptyState';
import {
  getHealth,
  listResearch,
  createResearch,
  getResearch,
  deleteResearch,
  getStreamUrl,
} from './api/client';
import type {
  HealthStatus,
  ResearchSummary,
  ResearchDetail,
  ResearchStage,
  SSEProgressEvent,
} from './types';
import { Loader2, AlertTriangle } from 'lucide-react';

export const App: React.FC = () => {
  // Backend & History State
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [history, setHistory] = useState<ResearchSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Active Research State
  const [isResearching, setIsResearching] = useState(false);
  const [currentStage, setCurrentStage] = useState<ResearchStage>('idle');
  const [activeTopic, setActiveTopic] = useState('');
  const [stageEvents, setStageEvents] = useState<SSEProgressEvent[]>([]);
  const [activeResearchId, setActiveResearchId] = useState<string | null>(null);
  const [generalError, setGeneralError] = useState<string | null>(null);

  // Selected / Completed Report State
  const [selectedDetail, setSelectedDetail] = useState<ResearchDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // SSE EventSource reference for clean unmounting
  const eventSourceRef = useRef<EventSource | null>(null);

  // Cleanup helper for SSE connections
  const closeEventSource = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  // Fetch Health Status
  const fetchHealth = useCallback(async () => {
    try {
      const data = await getHealth();
      setHealth(data);
    } catch {
      setHealth({ status: 'error', database: 'disconnected', version: 'offline' });
    } finally {
      setHealthLoading(false);
    }
  }, []);

  // Fetch Research History
  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const items = await listResearch(50);
      setHistory(items);
    } catch (err: unknown) {
      console.warn('Could not fetch research history:', err);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    const init = async () => {
      try {
        const [healthData, historyData] = await Promise.allSettled([
          getHealth(),
          listResearch(50),
        ]);
        if (!isMounted) return;

        if (healthData.status === 'fulfilled') {
          setHealth(healthData.value);
        } else {
          setHealth({ status: 'error', database: 'disconnected', version: 'offline' });
        }
        setHealthLoading(false);

        if (historyData.status === 'fulfilled') {
          setHistory(historyData.value);
        }
        setHistoryLoading(false);
      } catch {
        if (!isMounted) return;
        setHealthLoading(false);
        setHistoryLoading(false);
      }
    };

    void init();

    const interval = setInterval(fetchHealth, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
      closeEventSource();
    };
  }, [fetchHealth, closeEventSource]);

  // Handle Starting New Research
  const handleStartResearch = async (topic: string) => {
    closeEventSource();
    setGeneralError(null);
    setSelectedDetail(null);
    setActiveTopic(topic);
    setCurrentStage('started');
    setStageEvents([]);
    setIsResearching(true);

    try {
      // 1. Submit topic to POST /api/research
      const createRes = await createResearch(topic);
      const runId = createRes.id;
      setActiveResearchId(runId);

      // 2. Open EventSource for live SSE streaming
      const streamUrl = getStreamUrl(runId);
      const es = new EventSource(streamUrl);
      eventSourceRef.current = es;

      const appendEvent = (stage: ResearchStage, data: Record<string, unknown>) => {
        setCurrentStage(stage);
        const ev: SSEProgressEvent = {
          stage,
          id: String(data.id || runId),
          topic: String(data.topic || topic),
          message: typeof data.message === 'string' ? data.message : undefined,
          report: typeof data.report === 'string' ? data.report : undefined,
          feedback: typeof data.feedback === 'string' ? data.feedback : undefined,
          error: typeof data.error === 'string' ? data.error : undefined,
          timestamp: new Date().toISOString(),
        };
        setStageEvents((prev) => [...prev, ev]);
      };

      // Register stage-specific event listeners
      const stages: ResearchStage[] = [
        'started',
        'searching',
        'reading',
        'writing',
        'reviewing',
        'completed',
        'failed',
      ];

      stages.forEach((stageName) => {
        es.addEventListener(stageName, async (e: MessageEvent) => {
          try {
            const parsed = JSON.parse(e.data);
            appendEvent(stageName, parsed);

            if (stageName === 'completed') {
              closeEventSource();
              setIsResearching(false);
              // Fetch full detail and refresh history
              try {
                const detail = await getResearch(runId);
                setSelectedDetail(detail);
              } catch (detailErr) {
                console.error('Failed to load completed report:', detailErr);
              }
              fetchHistory();
            } else if (stageName === 'failed') {
              closeEventSource();
              setIsResearching(false);
              setGeneralError(parsed.error || 'Research pipeline encountered an error.');
              fetchHistory();
            }
          } catch (parseErr) {
            console.error('Error parsing SSE payload:', parseErr);
          }
        });
      });

      es.onerror = async () => {
        // Network connection dropped or stream closed
        closeEventSource();
        // Check if run actually finished in DB
        try {
          const detail = await getResearch(runId);
          if (detail && detail.status === 'completed') {
            setCurrentStage('completed');
            setIsResearching(false);
            setSelectedDetail(detail);
            fetchHistory();
            return;
          }
        } catch {
          // not ready
        }
        setIsResearching(false);
      };
    } catch (err: unknown) {
      closeEventSource();
      setIsResearching(false);
      setCurrentStage('failed');
      const msg = err instanceof Error ? err.message : 'Failed to launch research run.';
      setGeneralError(msg);
    }
  };

  // Reopen previous report from history
  const handleSelectRun = async (id: string) => {
    closeEventSource();
    setIsResearching(false);
    setGeneralError(null);
    setDetailLoading(true);
    setIsSidebarOpen(false);

    try {
      const detail = await getResearch(id);
      setSelectedDetail(detail);
      setActiveResearchId(id);
      setActiveTopic(detail.topic);
      setCurrentStage(detail.status);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load research report.';
      setGeneralError(msg);
    } finally {
      setDetailLoading(false);
    }
  };

  // Delete run
  const handleDeleteRun = async (id: string) => {
    try {
      await deleteResearch(id);
      if (selectedDetail?.id === id || activeResearchId === id) {
        closeEventSource();
        setSelectedDetail(null);
        setActiveResearchId(null);
        setIsResearching(false);
        setCurrentStage('idle');
      }
      fetchHistory();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete research run.';
      setGeneralError(msg);
    }
  };

  // Reset to New Research Form
  const handleNewResearch = () => {
    closeEventSource();
    setSelectedDetail(null);
    setActiveResearchId(null);
    setIsResearching(false);
    setCurrentStage('idle');
    setGeneralError(null);
    setStageEvents([]);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navigation Bar */}
      <Header
        health={health}
        healthLoading={healthLoading}
        onNewResearch={handleNewResearch}
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
        isSidebarOpen={isSidebarOpen}
      />

      {/* Main Layout Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Collapsible History Sidebar */}
        <Sidebar
          history={history}
          loading={historyLoading}
          selectedId={selectedDetail?.id || activeResearchId}
          onSelectRun={handleSelectRun}
          onDeleteRun={handleDeleteRun}
          onRefreshHistory={fetchHistory}
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
        />

        {/* Workspace Canvas */}
        <main className="flex-1 overflow-y-auto px-4 sm:px-6 md:px-8 py-8">
          <div className="max-w-5xl mx-auto space-y-8">
            {/* General Alert */}
            {generalError && (
              <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-200 flex items-start justify-between gap-3 shadow-lg">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                  <div className="text-xs sm:text-sm">
                    <p className="font-semibold text-rose-300">Notice</p>
                    <p className="mt-0.5 text-rose-200/90">{generalError}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setGeneralError(null)}
                  className="text-xs text-rose-400 hover:text-white underline font-medium"
                >
                  Dismiss
                </button>
              </div>
            )}

            {/* View 1: Loading Report Details */}
            {detailLoading ? (
              <div className="py-24 text-center space-y-3">
                <Loader2 className="w-8 h-8 animate-spin mx-auto text-indigo-400" />
                <p className="text-sm font-medium text-slate-400">Loading research report...</p>
              </div>
            ) : isResearching ? (
              /* View 2: Active Real-time SSE Progress */
              <div className="space-y-6">
                <ProgressTimeline
                  currentStage={currentStage}
                  topic={activeTopic}
                  events={stageEvents}
                  error={generalError}
                  onAbort={closeEventSource}
                />
              </div>
            ) : selectedDetail ? (
              /* View 3: Completed Report Viewer */
              <ReportViewer
                research={selectedDetail}
                onDelete={handleDeleteRun}
              />
            ) : (
              /* View 4: Default Start Research Workspace */
              <div className="space-y-10">
                <ResearchForm
                  onSubmit={handleStartResearch}
                  isLoading={isResearching}
                />
                <EmptyState />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;
