import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  FileText,
  Award,
  Globe,
  Copy,
  Check,
  Download,
  Trash2,
  Calendar,
  Layers,
  ExternalLink,
} from 'lucide-react';
import type { ResearchDetail } from '../types';

interface ReportViewerProps {
  research: ResearchDetail;
  onDelete: (id: string) => void;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({ research, onDelete }) => {
  const [activeTab, setActiveTab] = useState<'report' | 'critic' | 'sources'>('report');
  const [copied, setCopied] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleCopy = () => {
    if (research.report) {
      navigator.clipboard.writeText(research.report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (!research.report) return;
    const blob = new Blob([research.report], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const cleanTopic = research.topic.replace(/[^a-zA-Z0-9_-]/g, '_').substring(0, 40);
    link.download = `research_report_${cleanTopic}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Extract URLs from search results and scraped content safely
  const extractUrls = (text?: string | null): string[] => {
    if (!text) return [];
    const urlRegex = /(https?:\/\/[^\s"',]+)/g;
    const matches = text.match(urlRegex) || [];
    return Array.from(new Set(matches)).filter((u) => {
      try {
        const parsed = new URL(u);
        return parsed.protocol === 'http:' || parsed.protocol === 'https:';
      } catch {
        return false;
      }
    });
  };

  const detectedUrls = Array.from(
    new Set([
      ...extractUrls(research.search_results),
      ...extractUrls(research.scraped_content),
    ])
  );

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6">
      {/* Top Card: Meta & Actions */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 sm:p-7 shadow-xl backdrop-blur-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-800/40">
                Completed
              </span>
              <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
                <Calendar className="w-3.5 h-3.5" />
                {new Date(research.created_at).toLocaleString()}
              </span>
              <span className="text-xs text-slate-500 font-mono hidden sm:inline-block">
                ID: {research.id.slice(0, 8)}...
              </span>
            </div>

            <h1 className="text-xl sm:text-2xl md:text-3xl font-extrabold text-white leading-tight">
              {research.topic}
            </h1>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white transition-colors"
              title="Copy markdown report to clipboard"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              type="button"
              onClick={handleDownload}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white transition-colors"
              title="Download markdown report file"
            >
              <Download className="w-4 h-4" />
              <span>Download .md</span>
            </button>

            {isDeleting ? (
              <div className="flex items-center gap-1.5 bg-rose-950/60 border border-rose-800/60 px-2 py-1 rounded-xl">
                <span className="text-xs text-rose-300 font-semibold">Delete?</span>
                <button
                  type="button"
                  onClick={() => onDelete(research.id)}
                  className="px-2 py-1 rounded text-xs bg-rose-600 text-white font-medium hover:bg-rose-500"
                >
                  Confirm
                </button>
                <button
                  type="button"
                  onClick={() => setIsDeleting(false)}
                  className="px-2 py-1 rounded text-xs bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setIsDeleting(true)}
                className="p-2 rounded-xl text-slate-400 hover:text-rose-400 border border-slate-800 hover:border-rose-900 bg-slate-900 hover:bg-rose-950/40 transition-colors"
                title="Delete this research run"
                aria-label="Delete this research run"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 mt-6 border-b border-slate-800">
          <button
            type="button"
            onClick={() => setActiveTab('report')}
            className={`flex items-center gap-2 pb-3 px-3 text-xs sm:text-sm font-semibold border-b-2 transition-all ${
              activeTab === 'report'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Research Report</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('critic')}
            className={`flex items-center gap-2 pb-3 px-3 text-xs sm:text-sm font-semibold border-b-2 transition-all ${
              activeTab === 'critic'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Award className="w-4 h-4" />
            <span>Critic Evaluation</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('sources')}
            className={`flex items-center gap-2 pb-3 px-3 text-xs sm:text-sm font-semibold border-b-2 transition-all ${
              activeTab === 'sources'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Globe className="w-4 h-4" />
            <span>Sources & Intelligence ({detectedUrls.length})</span>
          </button>
        </div>
      </div>

      {/* Tab 1: Final Research Report */}
      {activeTab === 'report' && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 sm:p-10 shadow-xl backdrop-blur-xl">
          {research.report ? (
            <article className="prose prose-invert prose-indigo max-w-none text-slate-200 leading-relaxed">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ ...props }) => (
                    <h1 className="text-2xl sm:text-3xl font-extrabold text-white mt-8 mb-4 border-b border-slate-800 pb-3" {...props} />
                  ),
                  h2: ({ ...props }) => (
                    <h2 className="text-xl sm:text-2xl font-bold text-slate-100 mt-6 mb-3" {...props} />
                  ),
                  h3: ({ ...props }) => (
                    <h3 className="text-lg sm:text-xl font-semibold text-slate-200 mt-4 mb-2" {...props} />
                  ),
                  p: ({ ...props }) => (
                    <p className="my-3 text-slate-300 leading-relaxed text-sm sm:text-base" {...props} />
                  ),
                  ul: ({ ...props }) => (
                    <ul className="list-disc list-inside space-y-1 my-3 text-slate-300 text-sm sm:text-base pl-2" {...props} />
                  ),
                  ol: ({ ...props }) => (
                    <ol className="list-decimal list-inside space-y-1 my-3 text-slate-300 text-sm sm:text-base pl-2" {...props} />
                  ),
                  li: ({ ...props }) => (
                    <li className="leading-relaxed" {...props} />
                  ),
                  strong: ({ ...props }) => (
                    <strong className="font-semibold text-white" {...props} />
                  ),
                  blockquote: ({ ...props }) => (
                    <blockquote className="border-l-4 border-indigo-500 bg-indigo-950/20 py-2 px-4 rounded-r-lg my-4 text-slate-300 italic" {...props} />
                  ),
                  code: ({ ...props }) => (
                    <code className="bg-slate-950 px-1.5 py-0.5 rounded text-indigo-300 font-mono text-xs sm:text-sm border border-slate-800" {...props} />
                  ),
                  a: ({ href, children, ...props }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-400 hover:text-indigo-300 underline underline-offset-2 transition-colors font-medium inline-flex items-center gap-1"
                      {...props}
                    >
                      <span>{children}</span>
                      <ExternalLink className="w-3 h-3 inline-block opacity-75" />
                    </a>
                  ),
                }}
              >
                {research.report}
              </ReactMarkdown>
            </article>
          ) : (
            <p className="text-slate-400 text-sm italic">No report content available for this run.</p>
          )}
        </div>
      )}

      {/* Tab 2: Critic Evaluation */}
      {activeTab === 'critic' && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl backdrop-blur-xl space-y-4">
          <div className="flex items-center gap-2 pb-4 border-b border-slate-800 text-slate-200">
            <Award className="w-5 h-5 text-amber-400" />
            <h2 className="text-lg font-bold">Critic Agent Review & Recommendations</h2>
          </div>

          {research.feedback ? (
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 text-slate-200 font-sans text-sm sm:text-base whitespace-pre-wrap leading-relaxed">
              {research.feedback}
            </div>
          ) : (
            <p className="text-slate-400 text-sm italic">No critic feedback recorded.</p>
          )}
        </div>
      )}

      {/* Tab 3: Sources & Raw Intelligence */}
      {activeTab === 'sources' && (
        <div className="space-y-6">
          {/* Detected URLs */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-xl">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
              <Globe className="w-4 h-4 text-cyan-400" />
              Verified Discovered Sources ({detectedUrls.length})
            </h3>

            {detectedUrls.length > 0 ? (
              <div className="grid grid-cols-1 gap-2">
                {detectedUrls.map((url, idx) => (
                  <a
                    key={idx}
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-950 text-xs sm:text-sm text-cyan-300 hover:text-cyan-200 transition-colors group"
                  >
                    <span className="truncate mr-3 font-mono">{url}</span>
                    <ExternalLink className="w-4 h-4 shrink-0 text-slate-500 group-hover:text-cyan-400 transition-colors" />
                  </a>
                ))}
              </div>
            ) : (
              <p className="text-slate-400 text-xs italic">No specific external URLs extracted.</p>
            )}
          </div>

          {/* Search Agent Output */}
          {research.search_results && (
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-xl">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                Raw Search Agent Findings
              </h3>
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 text-xs font-mono text-slate-300 max-h-80 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                {research.search_results}
              </div>
            </div>
          )}

          {/* Scraped Content Preview */}
          {research.scraped_content && (
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-xl">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-400" />
                Reader Agent Scraped Content Excerpt
              </h3>
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 text-xs font-mono text-slate-300 max-h-80 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                {research.scraped_content}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
