import React from 'react';
import { Globe, BookOpen, PenTool, Award, ShieldCheck, Zap, Database } from 'lucide-react';

export const EmptyState: React.FC = () => {
  const agentCards = [
    {
      title: 'Search Agent',
      desc: 'Formulates targeted web queries and discovers current primary data sources using Tavily Search.',
      icon: Globe,
      color: 'from-cyan-500/15 via-blue-500/10 to-transparent text-cyan-400 border-cyan-500/30 hover:border-cyan-500/60',
      badge: 'Step 1',
    },
    {
      title: 'Reader Agent',
      desc: 'Selects the highest authority links and scrapes full article text with multi-strategy fallbacks.',
      icon: BookOpen,
      color: 'from-emerald-500/15 via-teal-500/10 to-transparent text-emerald-400 border-emerald-500/30 hover:border-emerald-500/60',
      badge: 'Step 2',
    },
    {
      title: 'Writer Chain',
      desc: 'Synthesizes raw findings into an executive-ready, structured research report with Google Gemini.',
      icon: PenTool,
      color: 'from-indigo-500/15 via-purple-500/10 to-transparent text-indigo-400 border-indigo-500/30 hover:border-indigo-500/60',
      badge: 'Step 3',
    },
    {
      title: 'Critic Chain',
      desc: 'Conducts automated peer review, scores quality (1-10), and verifies in-text citation consistency.',
      icon: Award,
      color: 'from-amber-500/15 via-orange-500/10 to-transparent text-amber-400 border-amber-500/30 hover:border-amber-500/60',
      badge: 'Step 4',
    },
  ];

  return (
    <div className="w-full max-w-4xl mx-auto mt-8 sm:mt-12 pt-8 sm:pt-10 border-t border-slate-800/80 animate-fade-in-up">
      <div className="text-center mb-6 sm:mb-8 space-y-1">
        <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400">
          How Multi-Agent Autonomous Research Works
        </h3>
        <p className="text-xs text-slate-500">
          Four specialized LangChain agents work in a coordinated autonomous workflow
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 sm:gap-4">
        {agentCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className={`p-4 sm:p-5 rounded-2xl border bg-gradient-to-b ${card.color} backdrop-blur-md space-y-3 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl group flex flex-col justify-between`}
            >
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-xl bg-slate-900/90 flex items-center justify-center border border-white/10 group-hover:scale-110 transition-transform">
                  <Icon className="w-4 h-4" />
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-900/80 text-slate-400 border border-slate-700/60 font-semibold">
                  {card.badge}
                </span>
              </div>

              <div>
                <h4 className="text-xs sm:text-sm font-bold text-white mb-1">{card.title}</h4>
                <p className="text-xs text-slate-300/85 leading-relaxed">{card.desc}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Architecture Highlights */}
      <div className="mt-8 sm:mt-10 flex flex-wrap items-center justify-center gap-4 sm:gap-8 text-xs text-slate-400 font-medium">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/70 border border-slate-800/80 shadow-sm">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Local SQLite Persistence (WAL)</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/70 border border-slate-800/80 shadow-sm">
          <Zap className="w-4 h-4 text-indigo-400 animate-pulse" />
          <span>Real-time SSE Streaming</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/70 border border-slate-800/80 shadow-sm">
          <Globe className="w-4 h-4 text-cyan-400" />
          <span>Tavily Web Search Discovery</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/70 border border-slate-800/80 shadow-sm">
          <Database className="w-4 h-4 text-purple-400" />
          <span>1-to-1 Citation Normalization</span>
        </div>
      </div>
    </div>
  );
};
