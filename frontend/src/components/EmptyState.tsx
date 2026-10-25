import React from 'react';
import { Globe, BookOpen, PenTool, Award, ShieldCheck, Zap } from 'lucide-react';

export const EmptyState: React.FC = () => {
  const agentCards = [
    {
      title: 'Search Agent',
      desc: 'Formulates targeted web queries and discovers current data sources using Tavily Search.',
      icon: Globe,
      color: 'from-cyan-500/20 to-blue-500/20 text-cyan-400 border-cyan-500/30',
    },
    {
      title: 'Reader Agent',
      desc: 'Picks the highest authority links and scrapes full article text with multi-strategy fallbacks.',
      icon: BookOpen,
      color: 'from-emerald-500/20 to-teal-500/20 text-emerald-400 border-emerald-500/30',
    },
    {
      title: 'Writer Chain',
      desc: 'Synthesizes raw findings into an executive-ready, structured research report with Google Gemini.',
      icon: PenTool,
      color: 'from-indigo-500/20 to-purple-500/20 text-indigo-400 border-indigo-500/30',
    },
    {
      title: 'Critic Chain',
      desc: 'Conducts automated peer review, scores quality (1-10), and generates constructive critique.',
      icon: Award,
      color: 'from-amber-500/20 to-orange-500/20 text-amber-400 border-amber-500/30',
    },
  ];

  return (
    <div className="w-full max-w-4xl mx-auto mt-12 pt-8 border-t border-slate-800/80">
      <div className="text-center mb-6">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          How Multi-Agent Autonomous Research Works
        </h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {agentCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className={`p-4 rounded-xl border bg-gradient-to-b ${card.color} backdrop-blur-sm space-y-2`}
            >
              <div className="w-8 h-8 rounded-lg bg-slate-900/80 flex items-center justify-center border border-white/10">
                <Icon className="w-4 h-4" />
              </div>
              <h4 className="text-xs font-bold text-white">{card.title}</h4>
              <p className="text-[11px] text-slate-300/90 leading-relaxed">{card.desc}</p>
            </div>
          );
        })}
      </div>

      <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-500 font-medium">
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Local SQLite Persistence</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Zap className="w-4 h-4 text-indigo-400" />
          <span>Real-time SSE Event Streaming</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Globe className="w-4 h-4 text-cyan-400" />
          <span>Tavily Real-time Web Discovery</span>
        </div>
      </div>
    </div>
  );
};
