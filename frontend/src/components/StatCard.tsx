import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'indigo' | 'cyan' | 'red' | 'amber' | 'emerald';
  trend?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'indigo',
  trend
}) => {
  const iconStyles = {
    indigo: 'bg-blue-50 border-blue-100 text-[#2563EB]',
    cyan: 'bg-sky-50 border-sky-100 text-sky-600',
    red: 'bg-red-50 border-red-100 text-[#DC2626]',
    amber: 'bg-amber-50 border-amber-100 text-[#F59E0B]',
    emerald: 'bg-emerald-50 border-emerald-100 text-[#16A34A]'
  }[color];

  return (
    <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {title}
        </p>
        <div className={`p-2 rounded-lg border ${iconStyles}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="mt-2 flex items-baseline justify-between">
        <h3 className="text-2xl font-black tracking-tight text-[#1E293B] font-mono">
          {value}
        </h3>
        {trend && (
          <span className="text-[11px] font-semibold text-slate-600 bg-slate-50 px-2 py-0.5 rounded-full border border-slate-200">
            {trend}
          </span>
        )}
      </div>
      {subtitle && (
        <p className="mt-1 text-xs text-slate-500 font-medium">
          {subtitle}
        </p>
      )}
    </div>
  );
};
