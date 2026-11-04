import { useId } from "react";

export default function ProgressRing({
  value,
  size = 88,
  strokeWidth = 8,
  showValue = true,
  tone = "default",
}: {
  value: number;
  size?: number;
  strokeWidth?: number;
  /** Show the percentage in the middle (turn off to draw your own). */
  showValue?: boolean;
  /** "onDark" draws a white ring for use on the purple gradient cards. */
  tone?: "default" | "onDark";
}) {
  const gradientId = useId();
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.min(100, Math.max(0, value));
  const offset = circumference - (clamped / 100) * circumference;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className={tone === "onDark" ? "text-white/20" : "text-muted/60"}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={tone === "onDark" ? "#ffffff" : `url(#${gradientId})`}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-500"
        />
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#f5a83c" />
            <stop offset="1" stopColor="#a855f7" />
          </linearGradient>
        </defs>
      </svg>
      {showValue && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={tone === "onDark" ? "num text-xl font-bold text-white" : "num text-lg font-bold text-foreground"}>{clamped}%</span>
        </div>
      )}
    </div>
  );
}
