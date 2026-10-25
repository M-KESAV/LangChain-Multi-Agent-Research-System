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

export const ProgressTimeline: React.FC<ProgressTimelineProps> = ({
  currentStage,
  topic,
  events,
  error,
  onAbort,
}) => {
  const currentStageIndex = STAGE_ORDER.indexOf(currentStage);
  const isFailed = currentStage === 'failed' || !!error;

  // Find latest message for current stage
  const latestEvent = events.length > 0 ? events[events.length - 1] : null;

  return (
    <div className="w-full max-w-4xl mx-auto bg-slate-900/90 border border-slate-800 rounded-2xl p-5 sm:p-7 shadow-xl backdrop-blur-xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="flex items-center gap-1.5 text-xs font-semibold text-cyan-400 bg-cyan-950/60 border border-cyan-800/40 px-2.5 py-0.5 rounded-full">
              <Radio className="w-3 h-3 animate-pulse" />
              Live SSE Research Stream
            </span>
            <span className="text-xs text-slate-500 font-mono">
              Stage {Math.max(1, currentStageIndex + 1)} of {STAGE_ORDER.length}
            </span>
          </div>

          <h2 className="text-base sm:text-lg font-bold text-white line-clamp-1">
            {topic}
          </h2>
        </div>

        {onAbort && currentStage !== 'completed' && !isFailed && (
          <button
            type="button"
            onClick={onAbort}
            className="text-xs font-medium px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800/80 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors self-start sm:self-auto"
          >
            Disconnect Stream
          </button>
        )}
      </div>

      {/* Error Banner */}
      {isFailed && (
        <div className="my-5 p-4 rounded-xl bg-rose-950/50 border border-rose-800/60 text-rose-200 flex items-start gap-3">
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
      <div className="mt-6 space-y-3 sm:space-y-4">
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
              className={`flex items-start gap-3.5 p-3.5 rounded-xl border transition-all ${
                isCurrent
                  ? 'bg-indigo-950/40 border-indigo-500/50 shadow-md shadow-indigo-500/10'
                  : isPassed
                  ? 'bg-slate-950/50 border-slate-800/80 text-slate-300'
                  : isThisFailed
                  ? 'bg-rose-950/40 border-rose-500/50'
                  : 'bg-slate-950/20 border-slate-800/40 opacity-50'
              }`}
            >
              {/* Step Icon */}
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border transition-colors ${
                  isCurrent
                    ? 'bg-indigo-600 border-indigo-400 text-white shadow-sm'
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
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <h3
                      className={`text-xs sm:text-sm font-semibold ${
                        isCurrent ? 'text-white' : isPassed ? 'text-slate-200' : 'text-slate-400'
                      }`}
                    >
                      {stage.label}
                    </h3>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
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
                    <span className="text-[11px] font-medium text-emerald-400">
                      Completed
                    </span>
                  )}
                </div>

                <p
                  className={`mt-1 text-xs leading-relaxed ${
                    isCurrent ? 'text-indigo-200/90 font-medium' : 'text-slate-400'
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
