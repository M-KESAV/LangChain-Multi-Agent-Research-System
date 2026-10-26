import React from 'react';
import {
  Globe,
  BookOpen,
  PenTool,
  CheckCircle2,
  XCircle,
  Loader2,
  Play,
  Award,
  Radio,
} from 'lucide-react';
import type { ResearchStage, SSEProgressEvent } from '../types';

interface ProgressTimelineProps {
  currentStage: ResearchStage;
  topic: string;
  events: SSEProgressEvent[];
  error?: string | null;
  onAbort?: () => void;
}

interface StageStep {
  key: ResearchStage;
  label: string;
  agent: string;
  description: string;
  icon: React.ElementType;
}

const STAGES: StageStep[] = [
  {
    key: 'started',
    label: 'Pipeline Initialized',
    agent: 'Orchestrator',
    description: 'Validating topic and initializing agent state',
    icon: Play,
  },
  {
    key: 'searching',
    label: 'Web Discovery',
    agent: 'Search Agent',
    description: 'Querying Tavily for relevant articles and publications',
    icon: Globe,
  },
  {
    key: 'reading',
    label: 'Content Extraction',
    agent: 'Reader Agent',
    description: 'Scraping and analyzing high-value URLs and sources',
    icon: BookOpen,
  },
  {
    key: 'writing',
    label: 'Report Synthesis',
    agent: 'Writer Chain',
    description: 'Drafting structured research report with Gemini',
    icon: PenTool,
  },
  {
    key: 'reviewing',
    label: 'Peer Review & Evaluation',
    agent: 'Critic Chain',
    description: 'Scoring report quality and suggesting improvements',
    icon: Award,
  },
  {
    key: 'completed',
    label: 'Research Finalized',
    agent: 'Storage & DB',
    description: 'Persisted to SQLite database and delivered to client',
    icon: CheckCircle2,
  },
];

const STAGE_ORDER: ResearchStage[] = [
  'started',
  'searching',
  'reading',
  'writing',
  'reviewing',
  'completed',
];

const STAGE_PERCENTAGES: Record<ResearchStage, number> = {
  idle: 0,
  started: 15,
  searching: 35,
  reading: 55,
  writing: 75,
  reviewing: 90,
  completed: 100,
  failed: 100,
  running: 50,
};

export const ProgressTimeline: React.FC<ProgressTimelineProps> = ({
  currentStage,
  topic,
  events,
  error,
  onAbort,
}) => {
  const currentStageIndex = STAGE_ORDER.indexOf(currentStage);
  const isFailed = currentStage === 'failed' || !!error;
  const progressPercent = STAGE_PERCENTAGES[currentStage] || 0;

  // Find latest message for current stage
  const latestEvent = events.length > 0 ? events[events.length - 1] : null;

  return (
    <div className="w-full max-w-4xl mx-auto bg-slate-900/90 border border-slate-800 rounded-2xl sm:rounded-3xl p-4 sm:p-7 shadow-2xl backdrop-blur-2xl animate-fade-in-up">
      {/* Header */}
      <div className="pb-5 sm:pb-6 border-b border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <span className="flex items-center gap-1.5 text-xs font-semibold text-cyan-400 bg-cyan-950/60 border border-cyan-800/40 px-2.5 py-0.5 rounded-full shadow-sm">
                <Radio className="w-3 h-3 animate-pulse" />
                Live SSE Research Stream
              </span>
              <span className="text-xs text-slate-500 font-mono">
                Stage {Math.max(1, currentStageIndex + 1)} of {STAGE_ORDER.length}
              </span>
            </div>

            <h2 className="text-base sm:text-xl font-bold text-white line-clamp-2 leading-snug">
              {topic}
            </h2>
          </div>

          {onAbort && currentStage !== 'completed' && !isFailed && (
            <button
              type="button"
              onClick={onAbort}
              className="text-xs font-medium px-3.5 py-2 rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors self-start sm:self-auto shrink-0"
            >
              Disconnect Stream
            </button>
          )}
        </div>

        {/* Dynamic Progress Bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center text-[11px] font-mono text-slate-400">
            <span>Overall Progress</span>
            <span className="font-semibold text-indigo-400">{progressPercent}%</span>
          </div>
          <div className="w-full h-2 rounded-full bg-slate-950 border border-slate-800/80 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ease-out rounded-full ${
                isFailed
                  ? 'bg-rose-500'
                  : 'bg-gradient-to-r from-indigo-500 via-cyan-400 to-emerald-400'
              }`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {isFailed && (
        <div className="my-5 p-4 rounded-xl bg-rose-950/60 border border-rose-800/70 text-rose-200 flex items-start gap-3 shadow-lg animate-fadeIn">
          <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="text-xs sm:text-sm">
            <p className="font-semibold text-rose-300">Research Pipeline Error</p>
            <p className="mt-1 text-rose-200/90 leading-relaxed">
              {error || latestEvent?.error || 'An error occurred during multi-agent research execution.'}
            </p>
          </div>
        </div>
      )}

      {/* Stages Stepper */}
      <div className="mt-6 space-y-3 sm:space-y-3.5">
        {STAGES.map((stage) => {
          const stepIndex = STAGE_ORDER.indexOf(stage.key);
          const isCurrent = currentStage === stage.key && !isFailed;
          const isPassed = !isFailed && currentStageIndex > stepIndex;
          const isThisFailed = isFailed && currentStage === stage.key;

          const IconComponent = stage.icon;

          // Find specific backend message received for this stage
          const stageEvent = events.find((e) => e.stage === stage.key);
          const stageMessage = stageEvent?.message || stage.description;

          return (
            <div
              key={stage.key}
              className={`flex items-start gap-3 sm:gap-4 p-3.5 sm:p-4 rounded-xl sm:rounded-2xl border transition-all duration-200 ${
                isCurrent
                  ? 'bg-indigo-950/40 border-indigo-500/70 shadow-lg shadow-indigo-500/10 ring-1 ring-indigo-500/30'
                  : isPassed
                  ? 'bg-slate-950/50 border-slate-800/80 text-slate-300'
                  : isThisFailed
                  ? 'bg-rose-950/40 border-rose-500/60'
                  : 'bg-slate-950/20 border-slate-800/40 opacity-50'
              }`}
            >
              {/* Step Icon */}
              <div
                className={`w-9 h-9 sm:w-10 sm:h-10 rounded-xl flex items-center justify-center shrink-0 border transition-all duration-300 ${
                  isCurrent
                    ? 'bg-indigo-600 border-indigo-400 text-white shadow-md shadow-indigo-600/30 ring-2 ring-indigo-500/30'
                    : isPassed
                    ? 'bg-emerald-950/80 border-emerald-700/60 text-emerald-400'
                    : isThisFailed
                    ? 'bg-rose-900 border-rose-600 text-rose-200'
                    : 'bg-slate-800 border-slate-700 text-slate-500'
                }`}
              >
                {isCurrent ? (
                  <Loader2 className="w-5 h-5 animate-spin text-white" />
                ) : isPassed ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                ) : isThisFailed ? (
                  <XCircle className="w-5 h-5 text-rose-400" />
                ) : (
                  <IconComponent className="w-4 h-4" />
                )}
              </div>

              {/* Step Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2">
                    <h3
                      className={`text-xs sm:text-sm font-bold ${
                        isCurrent ? 'text-white' : isPassed ? 'text-slate-200' : 'text-slate-400'
                      }`}
                    >
                      {stage.label}
                    </h3>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 font-medium">
                      {stage.agent}
                    </span>
                  </div>

                  {isCurrent && (
                    <span className="text-[11px] font-semibold text-indigo-400 animate-pulse flex items-center gap-1">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      Active
                    </span>
                  )}
                  {isPassed && (
                    <span className="text-[11px] font-medium text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      Completed
                    </span>
                  )}
                </div>

                <p
                  className={`mt-1 text-xs leading-relaxed ${
                    isCurrent ? 'text-indigo-200 font-medium' : 'text-slate-400'
                  }`}
                >
                  {stageMessage}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
