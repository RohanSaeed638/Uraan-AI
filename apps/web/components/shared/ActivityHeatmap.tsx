import { cn } from "@/lib/utils";

export type ActivityDay = { date: string; count: number; xp: number };

const WEEKS = 18;
const LEVELS = [
  "bg-muted",
  "bg-brand-violet/25",
  "bg-brand-violet/50",
  "bg-brand-violet/75",
  "bg-brand-violet",
];

const level = (count: number) => (count <= 0 ? 0 : count < 2 ? 1 : count < 4 ? 2 : count < 7 ? 3 : 4);

// A GitHub-style grid: one column per week, one square per day, darker for busier days.
// Rendered on the server, so it is plain markup (no chart library, no hydration risk).
export default function ActivityHeatmap({
  days,
  label,
  dayLabel,
  today = new Date(),
}: {
  days: ActivityDay[];
  label: string;
  dayLabel: (date: string, count: number) => string;
  today?: Date;
}) {
  const byDate = new Map(days.map((d) => [d.date, d.count]));
  const end = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()));
  // Start on the Sunday WEEKS-1 weeks before this week's Sunday.
  const start = new Date(end);
  start.setUTCDate(end.getUTCDate() - end.getUTCDay() - (WEEKS - 1) * 7);

  const columns: { date: string; count: number; future: boolean }[][] = [];

  for (let w = 0; w < WEEKS; w++) {
    const column = [];

    for (let d = 0; d < 7; d++) {
      const day = new Date(start);
      day.setUTCDate(start.getUTCDate() + w * 7 + d);
      const key = day.toISOString().slice(0, 10);
      column.push({ date: key, count: byDate.get(key) ?? 0, future: day > end });
    }

    columns.push(column);
  }

  return (
    <div role="img" aria-label={label} className="overflow-x-auto">
      <div className="flex w-max gap-1">
        {columns.map((column, w) => (
          <div key={w} className="flex flex-col gap-1">
            {column.map((cell) =>
              cell.future ? (
                <span key={cell.date} className="size-3.5" />
              ) : (
                <span
                  key={cell.date}
                  title={dayLabel(cell.date, cell.count)}
                  className={cn("size-3.5 rounded-[3px]", LEVELS[level(cell.count)])}
                />
              )
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
