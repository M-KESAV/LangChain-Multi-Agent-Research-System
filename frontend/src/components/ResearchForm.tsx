import React, { useState } from 'react';
import { Sparkles, ArrowRight, Lightbulb, Loader2 } from 'lucide-react';

interface ResearchFormProps {
  onSubmit: (topic: string) => void;
  isLoading: boolean;
}

const SAMPLE_TOPICS = [
  'Impact of Autonomous AI Agents on the Global Job Market in 2026',
  'Breakthroughs in Solid-State Battery Tech and Commercial Readiness',
  'Quantum Computing Advances in Post-Quantum Cryptography',
  'Next-Generation Cancer Immunotherapy and mRNA Vaccine Trials',
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
    <div className="w-full max-w-4xl mx-auto">
      {/* Hero Title */}
      <div className="text-center mb-8 space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-sm">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          Multi-Agent Autonomous Research
        </div>
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-white">
          Deep Research. <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-cyan-400 to-emerald-400">Autonomous Intelligence.</span>
        </h1>
        <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto">
          Four specialized LangChain agents orchestrate search, deep scraping, synthesis, and peer review using Google Gemini and Tavily.
        </p>
      </div>

      {/* Main Input Form */}
      <form onSubmit={handleSubmit} className="relative group">
        <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 via-cyan-500 to-emerald-500 rounded-3xl blur-lg opacity-25 group-hover:opacity-40 transition duration-500 pointer-events-none" />

        <div className="relative bg-slate-900/90 border border-slate-800 rounded-2xl p-4 sm:p-5 shadow-2xl backdrop-blur-xl">
          <label htmlFor="topic-input" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Enter Research Topic or Objective
          </label>

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
            placeholder="e.g. Current status of fusion energy commercialization and key challenges in 2026..."
            className="w-full bg-slate-950/80 border border-slate-800/90 rounded-xl p-3.5 text-sm sm:text-base text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all resize-none disabled:opacity-50"
          />

          {error && (
            <p className="text-xs text-rose-400 mt-2 font-medium flex items-center gap-1">
              {error}
            </p>
          )}

          <div className="mt-4 flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
            <span className="text-xs text-slate-500 hidden sm:inline-block">
              Pro tip: Press <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">Ctrl+Enter</kbd> to submit
            </span>

            <button
              type="submit"
              disabled={isLoading || !topic.trim()}
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white shadow-lg shadow-indigo-600/25 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Researching...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Start Autonomous Research</span>
                  <ArrowRight className="w-4 h-4 ml-0.5" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Suggested Topic Chips */}
      <div className="mt-6">
        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium mb-3">
          <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
          <span>Explore Suggested Research Prompts:</span>
        </div>

        <div className="flex flex-wrap gap-2">
          {SAMPLE_TOPICS.map((sample, idx) => (
            <button
              key={idx}
              type="button"
              disabled={isLoading}
              onClick={() => selectSampleTopic(sample)}
              className="text-left text-xs bg-slate-900/60 hover:bg-slate-800/80 active:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
            >
              {sample}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
