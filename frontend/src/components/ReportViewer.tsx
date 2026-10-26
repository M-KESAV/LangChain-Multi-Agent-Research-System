import React, { useState, useMemo } from 'react';
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
  Search,
  ShieldCheck,
  BookOpen,
} from 'lucide-react';
import type { ResearchDetail, SourceItem } from '../types';

interface ReportViewerProps {
  research: ResearchDetail;
  onDelete: (id: string) => void;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({ research, onDelete }) => {
  const [activeTab, setActiveTab] = useState<'report' | 'critic' | 'sources'>('report');
  const [copied, setCopied] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [sourceSearch, setSourceSearch] = useState('');

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

  const sourcesList = useMemo(() => {
    const list: SourceItem[] = [];
    const seen = new Set<string>();

    if (Array.isArray(research.sources)) {
      for (const s of research.sources) {
        if (s && s.url && !seen.has(s.url)) {
          seen.add(s.url);
          list.push(s);
        }
      }
    }

    const detected = [
      ...extractUrls(research.search_results),
      ...extractUrls(research.scraped_content),
      ...extractUrls(research.report),
    ];
    for (const u of detected) {
      if (!seen.has(u)) {
        seen.add(u);
        list.push({ url: u, title: u, status: 'discovered' });
      }
    }

    return list;
  }, [research.sources, research.search_results, research.scraped_content, research.report]);

  const filteredSources = useMemo(() => {
    if (!sourceSearch.trim()) return sourcesList;
    const q = sourceSearch.toLowerCase();
    return sourcesList.filter(
      (s) =>
        (s.title && s.title.toLowerCase().includes(q)) ||
        (s.url && s.url.toLowerCase().includes(q)) ||
        (s.snippet && s.snippet.toLowerCase().includes(q))
    );
  }, [sourcesList, sourceSearch]);

  // Extract Score from Critic feedback if present
  const scoreMatch = useMemo(() => {
    if (!research.feedback) return null;
    const match = research.feedback.match(/Score:\s*(\d+(?:\.\d+)?)\s*\/\s*10/i);
    return match ? match[1] : null;
  }, [research.feedback]);

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6 animate-fade-in-up">
      {/* Top Header Card */}
      <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl sm:rounded-3xl p-5 sm:p-7 shadow-2xl backdrop-blur-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-800/40 shadow-sm flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                Completed
              </span>
              <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
                {new Date(research.created_at).toLocaleString()}
              </span>
              <span className="text-xs text-slate-500 font-mono hidden sm:inline-block">
                ID: {research.id.slice(0, 8)}...
              </span>
              {scoreMatch && (
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-950/60 text-amber-300 border border-amber-800/40 flex items-center gap-1 shadow-sm">
                  <Award className="w-3.5 h-3.5 text-amber-400" />
                  Rating: {scoreMatch}/10
                </span>
              )}
            </div>

            <h1 className="text-xl sm:text-2xl md:text-3xl font-extrabold text-white leading-tight">
              {research.topic}
            </h1>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 shrink-0 self-start lg:self-center flex-wrap">
            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold border border-slate-700 bg-slate-800/90 hover:bg-slate-750 text-slate-200 hover:text-white transition-all shadow-sm active:scale-95"
              title="Copy markdown report to clipboard"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              <span>{copied ? 'Copied!' : 'Copy'}</span>
            </button>

            <button
              type="button"
              onClick={handleDownload}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold border border-slate-700 bg-slate-800/90 hover:bg-slate-750 text-slate-200 hover:text-white transition-all shadow-sm active:scale-95"
              title="Download markdown report file"
            >
              <Download className="w-4 h-4" />
              <span>Download .md</span>
            </button>

            {isDeleting ? (
              <div className="flex items-center gap-1.5 bg-rose-950/70 border border-rose-800/70 px-2.5 py-1 rounded-xl shadow-lg animate-fadeIn">
                <span className="text-xs text-rose-300 font-semibold">Delete?</span>
                <button
                  type="button"
                  onClick={() => onDelete(research.id)}
                  className="px-2.5 py-1 rounded-lg text-xs bg-rose-600 text-white font-semibold hover:bg-rose-500 transition-colors"
                >
                  Confirm
                </button>
                <button
                  type="button"
                  onClick={() => setIsDeleting(false)}
                  className="px-2.5 py-1 rounded-lg text-xs bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setIsDeleting(true)}
                className="p-2 rounded-xl text-slate-400 hover:text-rose-400 border border-slate-800 hover:border-rose-900/60 bg-slate-900/80 hover:bg-rose-950/40 transition-colors"
                title="Delete this research run"
                aria-label="Delete this research run"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Tab Navigation (Responsive & Non-wrapping) */}
        <div className="flex items-center gap-1 sm:gap-2 mt-6 border-b border-slate-800 overflow-x-auto no-scrollbar whitespace-nowrap">
          <button
            type="button"
            onClick={() => setActiveTab('report')}
            className={`flex items-center gap-2 pb-3 px-3.5 text-xs sm:text-sm font-bold border-b-2 transition-all duration-200 shrink-0 ${
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
            className={`flex items-center gap-2 pb-3 px-3.5 text-xs sm:text-sm font-bold border-b-2 transition-all duration-200 shrink-0 ${
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
            className={`flex items-center gap-2 pb-3 px-3.5 text-xs sm:text-sm font-bold border-b-2 transition-all duration-200 shrink-0 ${
              activeTab === 'sources'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Globe className="w-4 h-4" />
            <span>Sources & Intelligence ({sourcesList.length})</span>
          </button>
        </div>
      </div>

      {/* Tab 1: Final Research Report */}
      {activeTab === 'report' && (
        <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl sm:rounded-3xl p-5 sm:p-10 shadow-2xl backdrop-blur-2xl">
          {research.report ? (
            <article className="prose prose-invert prose-indigo max-w-none text-slate-200 leading-relaxed">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ ...props }) => (
                    <h1 className="text-2xl sm:text-3xl font-extrabold text-white mt-8 mb-4 border-b border-slate-800 pb-3 tracking-tight" {...props} />
                  ),
                  h2: ({ ...props }) => (
                    <h2 className="text-xl sm:text-2xl font-bold text-slate-100 mt-7 mb-3 tracking-tight flex items-center gap-2" {...props} />
                  ),
                  h3: ({ ...props }) => (
                    <h3 className="text-lg sm:text-xl font-semibold text-slate-200 mt-5 mb-2" {...props} />
                  ),
                  p: ({ ...props }) => (
                    <p className="my-3.5 text-slate-300 leading-relaxed text-sm sm:text-base" {...props} />
                  ),
                  ul: ({ ...props }) => (
                    <ul className="list-disc list-inside space-y-1.5 my-3.5 text-slate-300 text-sm sm:text-base pl-2" {...props} />
                  ),
                  ol: ({ ...props }) => (
                    <ol className="list-decimal list-inside space-y-1.5 my-3.5 text-slate-300 text-sm sm:text-base pl-2" {...props} />
                  ),
                  li: ({ ...props }) => (
                    <li className="leading-relaxed text-slate-300" {...props} />
                  ),
                  strong: ({ ...props }) => (
                    <strong className="font-bold text-white" {...props} />
                  ),
                  blockquote: ({ ...props }) => (
                    <blockquote className="border-l-4 border-indigo-500 bg-indigo-950/30 py-2.5 px-4 rounded-r-xl my-4 text-slate-200 italic shadow-sm" {...props} />
                  ),
                  pre: ({ ...props }) => (
                    <pre className="bg-slate-950 p-3 sm:p-4 rounded-xl text-indigo-300 font-mono text-xs sm:text-sm border border-slate-800 overflow-x-auto my-4 max-w-full" {...props} />
                  ),
                  code: ({ ...props }) => (
                    <code className="bg-slate-950 px-2 py-0.5 rounded-md text-indigo-300 font-mono text-xs sm:text-sm border border-slate-800 break-words" {...props} />
                  ),
                  img: ({ ...props }) => (
                    <img className="rounded-xl max-w-full h-auto shadow-lg my-4" {...props} />
                  ),
                  table: ({ ...props }) => (
                    <div className="overflow-x-auto my-6 rounded-xl border border-slate-800 max-w-full">
                      <table className="min-w-full divide-y divide-slate-800 text-left text-xs sm:text-sm" {...props} />
                    </div>
                  ),
                  th: ({ ...props }) => (
                    <th className="bg-slate-950 px-4 py-3 font-semibold text-white uppercase tracking-wider text-xs" {...props} />
                  ),
                  td: ({ ...props }) => (
                    <td className="px-4 py-3 border-t border-slate-800/60 text-slate-300" {...props} />
                  ),
                  a: ({ href, children, ...props }) => {
                    const isCitation = typeof children === 'string' && /^\[?\d+\]?$/.test(children.trim());
                    if (isCitation) {
                      return (
                        <a
                          href={href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="citation-pill"
                          title={`Source reference ${children}`}
                          {...props}
                        >
                          {children}
                        </a>
                      );
                    }
                    return (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2 transition-colors font-medium inline-flex items-center gap-1"
                        {...props}
                      >
                        <span>{children}</span>
                        <ExternalLink className="w-3 h-3 inline-block opacity-75 shrink-0" />
                      </a>
                    );
                  },
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
        <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl sm:rounded-3xl p-5 sm:p-8 shadow-2xl backdrop-blur-2xl space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
            <div className="flex items-center gap-2.5 text-slate-200">
              <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                <Award className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base sm:text-lg font-bold text-white">Critic Agent Review & Recommendations</h2>
                <p className="text-xs text-slate-400">Objective automated peer evaluation & source consistency review</p>
              </div>
            </div>

            {scoreMatch && (
              <div className="flex items-center gap-2 bg-slate-950 px-3.5 py-1.5 rounded-xl border border-slate-800 self-start sm:self-auto">
                <span className="text-xs text-slate-400">Evaluation Score:</span>
                <span className="text-sm font-extrabold text-amber-400">{scoreMatch} / 10</span>
              </div>
            )}
          </div>

          {research.feedback ? (
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 sm:p-6 text-slate-200 font-sans text-xs sm:text-sm whitespace-pre-wrap leading-relaxed shadow-inner">
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
          {/* Verified Discovered Sources Card */}
          <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl sm:rounded-3xl p-5 sm:p-7 shadow-2xl backdrop-blur-2xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Globe className="w-4 h-4 text-cyan-400" />
                Verified Discovered Sources ({sourcesList.length})
              </h3>

              {sourcesList.length > 3 && (
                <div className="relative w-full sm:w-64">
                  <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    value={sourceSearch}
                    onChange={(e) => setSourceSearch(e.target.value)}
                    placeholder="Filter sources..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>
              )}
            </div>

            {filteredSources.length > 0 ? (
              <div className="grid grid-cols-1 gap-3">
                {filteredSources.map((src, idx) => {
                  const isScraped = src.status === 'scraped';
                  const isFailed = src.status === 'failed';

                  return (
                    <div
                      key={idx}
                      className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 hover:border-slate-750 transition-all duration-200 space-y-2 hover:shadow-md"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <a
                          href={src.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-bold text-xs sm:text-sm text-cyan-300 hover:text-cyan-200 hover:underline flex items-center gap-1.5 leading-snug group"
                        >
                          <span className="line-clamp-2">{src.title || src.url}</span>
                          <ExternalLink className="w-3.5 h-3.5 shrink-0 opacity-70 group-hover:opacity-100 text-slate-400 group-hover:text-cyan-300" />
                        </a>

                        <div className="shrink-0">
                          {isScraped ? (
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 shadow-sm flex items-center gap-1">
                              <BookOpen className="w-3 h-3" />
                              Scraped
                            </span>
                          ) : isFailed ? (
                            <span
                              className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-950/80 text-rose-400 border border-rose-800/60"
                              title={src.error || 'Scrape failed'}
                            >
                              Scrape Failed
                            </span>
                          ) : (
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
                              Discovered
                            </span>
                          )}
                        </div>
                      </div>

                      <p className="text-[11px] font-mono text-slate-500 truncate">
                        {src.url}
                      </p>

                      {src.snippet && (
                        <p className="text-xs text-slate-300/90 leading-relaxed pt-1 border-t border-slate-900">
                          {src.snippet}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-8 text-center text-slate-400 bg-slate-950/40 rounded-xl border border-slate-800/50 space-y-1">
                <p className="text-xs font-semibold text-slate-300">
                  {sourceSearch ? 'No sources match your filter' : 'No external source URLs discovered'}
                </p>
                <p className="text-[11px] text-slate-500">
                  {sourceSearch ? 'Try a different search keyword' : 'The pipeline could not verify external links for this topic.'}
                </p>
              </div>
            )}
          </div>

          {/* Search Agent Raw Findings */}
          {research.search_results && (
            <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl sm:rounded-3xl p-5 sm:p-7 shadow-2xl backdrop-blur-2xl">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                Raw Search Agent Findings
              </h3>
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 text-xs font-mono text-slate-300 max-h-80 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                {research.search_results}
              </div>
            </div>
          )}

          {/* Scraped Content Preview */}
          {research.scraped_content && (
            <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl sm:rounded-3xl p-5 sm:p-7 shadow-2xl backdrop-blur-2xl">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-400" />
                Reader Agent Scraped Content Excerpt
              </h3>
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 text-xs font-mono text-slate-300 max-h-80 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                {research.scraped_content}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
