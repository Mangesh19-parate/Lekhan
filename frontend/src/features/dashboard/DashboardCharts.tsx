import React, { useState } from "react";
import { FileText, Award, Clock, CheckCircle2, TrendingUp, Globe2 } from "lucide-react";
import { Badge } from "../../shared/components";

export interface DayData {
  date: string;
  label: string;
  count: number;
}

export interface LanguageData {
  lang: string;
  label: string;
  count: number;
  color: string;
}

export interface StatusData {
  status: "draft" | "under_review" | "approved" | "finalised";
  label: string;
  count: number;
  color: string;
}

interface DashboardChartsProps {
  timelineData?: DayData[];
  languageData?: { mr: number; en: number; hi?: number };
  statusData?: { draft: number; under_review: number; approved: number; finalised: number };
}

export const DashboardCharts: React.FC<DashboardChartsProps> = ({
  timelineData = [
    { date: "2026-11-10", label: "10 Nov", count: 3 },
    { date: "2026-11-11", label: "11 Nov", count: 7 },
    { date: "2026-11-12", label: "12 Nov", count: 12 },
    { date: "2026-11-13", label: "13 Nov", count: 9 },
    { date: "2026-11-14", label: "14 Nov", count: 16 },
    { date: "2026-11-15", label: "15 Nov", count: 14 },
    { date: "2026-11-16", label: "16 Nov", count: 22 },
  ],
  languageData = { mr: 18, en: 10 },
  statusData = { draft: 8, under_review: 6, approved: 12, finalised: 2 },
}) => {
  const [hoveredDay, setHoveredDay] = useState<DayData | null>(null);

  // 1. Documents per day calculation
  const maxDayCount = Math.max(...timelineData.map((d) => d.count), 1);
  const totalPeriodDocs = timelineData.reduce((acc, d) => acc + d.count, 0);

  // 2. Documents per language calculation
  const totalLang = (languageData.mr || 0) + (languageData.en || 0) + (languageData.hi || 0) || 1;
  const mrPct = Math.round(((languageData.mr || 0) / totalLang) * 100);
  const enPct = Math.round(((languageData.en || 0) / totalLang) * 100);
  const hiPct = Math.max(0, 100 - mrPct - enPct);

  // 3. Documents per status calculation
  const totalStatus =
    (statusData.draft || 0) +
    (statusData.under_review || 0) +
    (statusData.approved || 0) +
    (statusData.finalised || 0) || 1;

  const statuses: {
    key: "draft" | "under_review" | "approved" | "finalised";
    label: string;
    count: number;
    color: string;
    badgeVariant: "draft" | "under_review" | "approved" | "active";
  }[] = [
    {
      key: "approved",
      label: "Approved by Advocate",
      count: statusData.approved || 0,
      color: "var(--approved-500, #CBA258)",
      badgeVariant: "approved",
    },
    {
      key: "finalised",
      label: "Finalised & Registered",
      count: statusData.finalised || 0,
      color: "var(--brand-600, #006241)",
      badgeVariant: "active",
    },
    {
      key: "under_review",
      label: "In Lawyer Review",
      count: statusData.under_review || 0,
      color: "var(--warning-500, #FBBC05)",
      badgeVariant: "under_review",
    },
    {
      key: "draft",
      label: "Working Drafts",
      count: statusData.draft || 0,
      color: "var(--text-secondary, #515E59)",
      badgeVariant: "draft",
    },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 w-full">
      {/* Chart 1: Documents per day (Timeline Bar & Trend) */}
      <div className="bg-card border border-line-subtle rounded-card p-5 shadow-card flex flex-col justify-between">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <TrendingUp size={16} className="text-brand-600 dark:text-brand-400" />
              <h3 className="text-sm font-semibold text-text-primary font-ui">
                Documents per Day (7 Days)
              </h3>
            </div>
            <p className="text-xs text-text-secondary mt-0.5">
              Total created: <strong className="text-text-primary font-semibold">{totalPeriodDocs} deeds</strong>
            </p>
          </div>
          <span className="text-xs font-mono px-2 py-0.5 rounded-pill bg-brand-100 text-brand-700 dark:bg-brand-900/50 dark:text-brand-400 font-semibold">
            +32% vs last wk
          </span>
        </div>

        {/* Visual Bar Graph */}
        <div className="h-44 flex items-end justify-between gap-2 pt-6 pb-2 px-1 relative">
          {timelineData.map((d) => {
            const heightPct = Math.round((d.count / maxDayCount) * 100);
            const isHovered = hoveredDay?.date === d.date;

            return (
              <div
                key={d.date}
                className="flex-1 flex flex-col items-center h-full justify-end group cursor-pointer"
                onMouseEnter={() => setHoveredDay(d)}
                onMouseLeave={() => setHoveredDay(null)}
              >
                {/* Count Pill */}
                <span
                  className={`text-[11px] font-mono font-bold mb-1.5 transition-all ${
                    isHovered
                      ? "text-brand-600 dark:text-brand-400 scale-110"
                      : "text-text-secondary opacity-70 group-hover:opacity-100"
                  }`}
                >
                  {d.count}
                </span>

                {/* Bar */}
                <div className="w-full max-w-[28px] bg-sunken dark:bg-sunken/60 rounded-t-input h-full flex items-end overflow-hidden">
                  <div
                    style={{ height: `${heightPct}%` }}
                    className={`w-full transition-all duration-300 rounded-t-input ${
                      isHovered
                        ? "bg-brand-500 shadow-sm"
                        : "bg-brand-600/80 group-hover:bg-brand-500"
                    }`}
                  />
                </div>

                {/* X-Axis Label */}
                <span className="text-[10px] text-text-tertiary mt-2 font-ui whitespace-nowrap">
                  {d.label}
                </span>
              </div>
            );
          })}
        </div>

        <div className="pt-3 border-t border-line-subtle text-[11px] text-text-secondary flex justify-between items-center">
          <span>Daily drafting throughput</span>
          <span className="text-text-primary font-medium">Avg: {Math.round(totalPeriodDocs / 7)} / day</span>
        </div>
      </div>

      {/* Chart 2: Documents per language (Bilingual Ratio) */}
      <div className="bg-card border border-line-subtle rounded-card p-5 shadow-card flex flex-col justify-between">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Globe2 size={16} className="text-brand-600 dark:text-brand-400" />
            <h3 className="text-sm font-semibold text-text-primary font-ui">
              Documents per Language
            </h3>
          </div>
          <span className="text-xs text-text-secondary font-ui">
            Total: <strong className="text-text-primary">{totalLang}</strong>
          </span>
        </div>

        {/* Donut representation */}
        <div className="flex items-center justify-center py-4">
          <div className="relative w-36 h-36 flex items-center justify-center">
            {/* SVG Ring */}
            <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
              {/* Background circle */}
              <circle
                cx="18"
                cy="18"
                r="15.915"
                fill="transparent"
                stroke="var(--surface-sunken)"
                strokeWidth="3.8"
              />
              {/* Marathi segment */}
              <circle
                cx="18"
                cy="18"
                r="15.915"
                fill="transparent"
                stroke="var(--brand-600, #006241)"
                strokeWidth="3.8"
                strokeDasharray={`${mrPct} ${100 - mrPct}`}
                strokeDashoffset="0"
                strokeLinecap="round"
                className="transition-all duration-500"
              />
              {/* English segment */}
              <circle
                cx="18"
                cy="18"
                r="15.915"
                fill="transparent"
                stroke="var(--brand-400, #108E5F)"
                strokeWidth="3.8"
                strokeDasharray={`${enPct} ${100 - enPct}`}
                strokeDashoffset={`-${mrPct}`}
                strokeLinecap="round"
                className="transition-all duration-500"
              />
            </svg>

            {/* Center metric */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
              <span className="text-xl font-bold text-text-primary font-ui leading-none">
                {mrPct}%
              </span>
              <span className="text-[10px] text-text-secondary mt-1 font-ui uppercase tracking-wider">
                मराठी (MR)
              </span>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="space-y-2 pt-3 border-t border-line-subtle text-xs font-ui">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-brand-600 shrink-0" />
              <span className="text-text-primary font-medium">मराठी (Marathi)</span>
            </div>
            <span className="font-mono text-text-secondary">
              {languageData.mr || 0} ({mrPct}%)
            </span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-brand-400 shrink-0" />
              <span className="text-text-primary font-medium">English (इंग्रजी)</span>
            </div>
            <span className="font-mono text-text-secondary">
              {languageData.en || 0} ({enPct}%)
            </span>
          </div>
        </div>
      </div>

      {/* Chart 3: Documents per status */}
      <div className="bg-card border border-line-subtle rounded-card p-5 shadow-card flex flex-col justify-between">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} className="text-brand-600 dark:text-brand-400" />
            <h3 className="text-sm font-semibold text-text-primary font-ui">
              Documents per Status (FSM)
            </h3>
          </div>
          <span className="text-xs text-text-secondary font-ui">
            Workflow Stages
          </span>
        </div>

        {/* Status progress list */}
        <div className="space-y-3.5 my-auto">
          {statuses.map((st) => {
            const pct = Math.round((st.count / totalStatus) * 100);

            return (
              <div key={st.key} className="space-y-1">
                <div className="flex items-center justify-between text-xs font-ui">
                  <span className="font-medium text-text-primary">{st.label}</span>
                  <span className="font-mono font-semibold text-text-secondary">
                    {st.count} ({pct}%)
                  </span>
                </div>
                {/* Horizontal Progress Bar */}
                <div className="w-full h-2 rounded-pill bg-sunken dark:bg-sunken/60 overflow-hidden">
                  <div
                    style={{ width: `${pct}%`, backgroundColor: st.color }}
                    className="h-full rounded-pill transition-all duration-500"
                  />
                </div>
              </div>
            );
          })}
        </div>

        <div className="pt-3 border-t border-line-subtle text-[11px] text-text-secondary flex justify-between items-center">
          <span>Advocate Sign-Off Rate</span>
          <span className="text-text-primary font-semibold">
            {Math.round(((statusData.approved + statusData.finalised) / totalStatus) * 100)}%
          </span>
        </div>
      </div>
    </div>
  );
};
