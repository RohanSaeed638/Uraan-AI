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
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <p className="text-sm text-muted-foreground">
        {label}
      </p>

      <h3 className="mt-1 font-semibold text-lg">
        {value}
      </h3>
    </div>
  );
}