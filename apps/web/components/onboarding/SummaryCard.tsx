"use client";

interface SummaryCardProps {
  label: string;
  value: string | number;
}

export default function SummaryCard({
  label,
  value,
}: SummaryCardProps) {
  return (
    <div className="rounded-2xl border border-border bg-muted/40 p-4">
      <p className="text-sm text-muted-foreground">
        {label}
      </p>

      <h3 className="mt-1 text-lg font-semibold">
        {value}
      </h3>
    </div>
  );
}