import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface Props {
  title: string;
  subtitle?: string;
  illustration?: ReactNode;
  children: ReactNode;
  className?: string;
}

export default function OnboardingCard({
  title,
  subtitle,
  illustration,
  children,
  className,
}: Props) {
  return (
    <div
      className={cn(
        "mx-auto w-full max-w-4xl rounded-3xl border border-border bg-card p-8 shadow-sm sm:p-10",
        illustration && "sm:grid sm:grid-cols-[1fr_auto] sm:items-center sm:gap-8",
        className
      )}
    >
      <div className="min-w-0">
        <h1 className="font-heading text-2xl font-bold sm:text-3xl">
          {title}
        </h1>

        {subtitle && <p className="mt-2 text-muted-foreground">{subtitle}</p>}

        <div className="mt-8">{children}</div>
      </div>

      {illustration && (
        <div className="hidden shrink-0 self-center sm:block">
          {illustration}
        </div>
      )}
    </div>
  );
}
