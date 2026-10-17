interface Props {
  current: number;
  total: number;
  label?: string;
}

export default function StepIndicator({ current, total, label }: Props) {
  const progress = Math.round(((current + 1) / total) * 100);

  return (
    <div className="mb-8">
      <div className="mb-2.5 flex items-center justify-between text-sm">
        <span className="font-medium">
          Step {Math.min(current + 1, total)} of {total}
          {label && (
            <span className="text-muted-foreground"> · {label}</span>
          )}
        </span>
        <span className="text-muted-foreground">{progress}%</span>
      </div>

      <div className="flex gap-1.5">
        {Array.from({ length: total }).map((_, index) => (
          <div
            key={index}
            className={`h-1.5 flex-1 rounded-full transition-all ${
              index <= current ? "bg-brand-gradient" : "bg-muted"
            }`}
          />
        ))}
      </div>
    </div>
  );
}
