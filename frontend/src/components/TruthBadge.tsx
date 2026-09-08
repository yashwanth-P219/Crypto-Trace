import React from 'react';
import { Database, Cpu, Brain, CheckSquare } from 'lucide-react';

export type TruthCategory = 'BLOCKCHAIN FACT' | 'SYSTEM INFERENCE' | 'AI ASSESSMENT' | 'INVESTIGATOR DECISION';

interface TruthBadgeProps {
  category: TruthCategory | string;
  size?: 'sm' | 'md';
}

export const TruthBadge: React.FC<TruthBadgeProps> = ({ category, size = 'md' }) => {
  const norm = category.toUpperCase();

  if (norm.includes('FACT')) {
    return (
      <span className={`inline-flex items-center gap-1 font-semibold rounded-md border ${
        size === 'sm' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs'
      } bg-emerald-50 text-emerald-700 border-emerald-200 shadow-xs`}>
        <Database className={size === 'sm' ? 'w-2.5 h-2.5' : 'w-3.5 h-3.5'} />
        BLOCKCHAIN FACT
      </span>
    );
  }

  if (norm.includes('INFERENCE') || norm.includes('PATTERN')) {
    return (
      <span className={`inline-flex items-center gap-1 font-semibold rounded-md border ${
        size === 'sm' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs'
      } bg-amber-50 text-amber-800 border-amber-200 shadow-xs`}>
        <Cpu className={size === 'sm' ? 'w-2.5 h-2.5' : 'w-3.5 h-3.5'} />
        SYSTEM INFERENCE
      </span>
    );
  }

  if (norm.includes('AI') || norm.includes('ASSESSMENT') || norm.includes('RISK')) {
    return (
      <span className={`inline-flex items-center gap-1 font-semibold rounded-md border ${
        size === 'sm' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs'
      } bg-purple-50 text-purple-700 border-purple-200 shadow-xs`}>
        <Brain className={size === 'sm' ? 'w-2.5 h-2.5' : 'w-3.5 h-3.5'} />
        AI ASSESSMENT
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1 font-semibold rounded-md border ${
      size === 'sm' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs'
    } bg-blue-50 text-blue-700 border-blue-200 shadow-xs`}>
      <CheckSquare className={size === 'sm' ? 'w-2.5 h-2.5' : 'w-3.5 h-3.5'} />
      INVESTIGATOR DECISION
    </span>
  );
};
