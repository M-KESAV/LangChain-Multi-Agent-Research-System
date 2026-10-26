import React, { useState } from 'react';
import { Sparkles, ArrowRight, Loader2, X, Compass } from 'lucide-react';

interface ResearchFormProps {
  onSubmit: (topic: string) => void;
  isLoading: boolean;
}

const SAMPLE_TOPICS = [
  {
    topic: 'Impact of Autonomous AI Agents on the Global Job Market in 2026',
    tag: 'Labor & Economics',
  },
  {
    topic: 'Breakthroughs in Solid-State Battery Tech and Commercial Readiness',
    tag: 'Clean Tech',
  },
  {
    topic: 'Quantum Computing Advances in Post-Quantum Cryptography',
    tag: 'Cybersecurity',
  },
  {
    topic: 'Next-Generation Cancer Immunotherapy and mRNA Vaccine Trials',
    tag: 'Biomedicine',
  },
];

export const ResearchForm: React.FC<ResearchFormProps> = ({ onSubmit, isLoading }) => {
  const [topic, setTopic] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic || !topic.trim()) {
      setError('Please enter a research topic to proceed.');
      return;
    }
    setError(null);
    onSubmit(topic.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  const selectSampleTopic = (sample: string) => {
    setTopic(sample);
    setError(null);
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8 animate-fade-in-up">
      {/* Hero Header */}
      <div className="text-center space-y-3 sm:space-y-4">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-gradient-to-r from-indigo-500/10 via-cyan-500/10 to-indigo-500/10 text-indigo-300 border border-indigo-500/25 shadow-sm backdrop-blur-md">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-spin" style={{ animationDuration: '6s' }} />
          <span>Multi-Agent Autonomous Research</span>
        </div>

        <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-black tracking-tight text-white leading-tight">
          Deep Research.{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-cyan-400 to-emerald-400 drop-shadow-sm">
            Autonomous Intelligence.
          </span>
        </h1>

        <p className="text-xs sm:text-sm md:text-base text-slate-400 max-w-2xl mx-auto leading-relaxed px-2">
          Specialized LangChain agents autonomously formulate web queries, extract primary sources with Tavily, synthesize structured reports with Gemini, and conduct peer review.
        </p>
      </div>

      {/* Main Input Card */}
      <form onSubmit={handleSubmit} className="relative group">
        {/* Ambient Gradient Glow */}
        <div className="absolute -inset-1 bg-gradient-to-r from-indigo-600 via-cyan-500 to-emerald-500 rounded-3xl blur-xl opacity-20 group-hover:opacity-35 transition duration-700 pointer-events-none" />

        <div className="relative bg-slate-900/90 border border-slate-800/90 rounded-2xl sm:rounded-3xl p-4 sm:p-6 shadow-2xl backdrop-blur-2xl">
          <div className="flex items-center justify-between mb-2">
            <label htmlFor="topic-input" className="block text-xs font-bold text-slate-400 uppercase tracking-wider">
              Enter Research Objective or Topic
            </label>
            {topic.length > 0 && (
              <span className="text-[11px] font-mono text-slate-500">
                {topic.length} chars
              </span>
            )}
          </div>

          <div className="relative">
            <textarea
              id="topic-input"
              rows={3}
              value={topic}
              onChange={(e) => {
                setTopic(e.target.value);
                if (error) setError(null);
              }}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder="e.g. Current status of fusion energy commercialization and key engineering challenges in 2026..."
              className="w-full bg-slate-950/80 border border-slate-800/90 rounded-xl p-3.5 sm:p-4 text-sm sm:text-base text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/80 transition-all resize-none disabled:opacity-50 pr-8"
            />
            {topic && !isLoading && (
              <button
                type="button"
                onClick={() => setTopic('')}
                className="absolute right-3 top-3 text-slate-500 hover:text-slate-300 p-1 rounded-md transition-colors"
                title="Clear input"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {error && (
            <p className="text-xs text-rose-400 mt-2 font-medium flex items-center gap-1.5 animate-fadeIn">
              {error}
            </p>
          )}

          <div className="mt-4 flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 border-t border-slate-800/40">
            <span className="text-xs text-slate-500 hidden sm:inline-flex items-center gap-1.5">
              <span>Pro tip: Press</span>
              <kbd className="px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-300 font-mono text-[10px] border border-slate-700">
                Ctrl+Enter
              </kbd>
              <span>to launch</span>
            </span>

            <button
              type="submit"
              disabled={isLoading || !topic.trim()}
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 sm:px-7 py-3 rounded-xl font-bold text-sm bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 active:scale-[0.98] text-white shadow-lg shadow-indigo-600/30 transition-all duration-200 disabled:opacity-50 disabled:pointer-events-none hover:shadow-indigo-500/40"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Orchestrating Agents...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-cyan-200" />
                  <span>Start Autonomous Research</span>
                  <ArrowRight className="w-4 h-4 ml-0.5 group-hover:translate-x-0.5 transition-transform" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Suggested Topic Chips */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-xs text-slate-400 font-semibold tracking-wide uppercase">
          <Compass className="w-4 h-4 text-amber-400" />
          <span>Explore Suggested Research Prompts:</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {SAMPLE_TOPICS.map((sample, idx) => (
            <button
              key={idx}
              type="button"
              disabled={isLoading}
              onClick={() => selectSampleTopic(sample.topic)}
              className="text-left p-3 rounded-xl bg-slate-900/60 hover:bg-slate-850 active:bg-slate-800 border border-slate-800/80 hover:border-indigo-500/40 text-slate-300 hover:text-white transition-all duration-200 group hover:-translate-y-0.5 hover:shadow-md flex flex-col justify-between gap-1.5"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-800/80 text-cyan-400 border border-slate-700/60 font-semibold">
                  {sample.tag}
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-indigo-400 group-hover:translate-x-0.5 transition-all" />
              </div>
              <p className="text-xs font-medium text-slate-200 leading-snug line-clamp-2">
                {sample.topic}
              </p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
