"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export type WeekPoint = { week: string; xp: number };

// XP earned per week. The chart is decorative for sighted users; the figures are
// also in the heatmap summary and the stat tiles, so it is hidden from screen readers.
export default function ActivityChart({ data, label }: { data: WeekPoint[]; label: string }) {
  return (
    <div className="h-56 w-full" aria-hidden>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
          <XAxis dataKey="week" tickLine={false} axisLine={false} fontSize={12} stroke="var(--muted-foreground)" />
          <YAxis allowDecimals={false} tickLine={false} axisLine={false} fontSize={12} stroke="var(--muted-foreground)" />
          <Tooltip
            cursor={{ fill: "var(--muted)" }}
            contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12 }}
            formatter={(value) => [value, label]}
          />
          <Bar dataKey="xp" fill="var(--chart-1)" radius={[6, 6, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
