"use client";

import { useTranslations } from "next-intl";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export interface Stage {
  label: string;
}

interface Props {
  stages: Stage[];
  activeStage: number; // 0-indexed
}

export default function StageIndicator({ stages, activeStage }: Props) {
  const t = useTranslations("onboarding");

  return (
    <div className="mx-auto mb-10 flex w-full max-w-2xl items-start">
      {stages.map((stage, index) => {
        const isComplete = index < activeStage;
        const isActive = index === activeStage;

        return (
          <div key={stage.label} className="flex flex-1 items-center last:flex-none">
            <div className="flex flex-col items-center gap-2">
              <div
                className={cn(
                  "flex size-8 shrink-0 items-center justify-center rounded-full border-2 text-xs font-semibold transition-colors",
                  isActive &&
                    "border-brand-gold bg-brand-gold text-[#241a05] ring-4 ring-brand-gold/25",
                  isComplete &&
                    "border-brand-gold bg-brand-gold/15 text-brand-gold-deep dark:text-brand-gold",
                  !isActive &&
                    !isComplete &&
                    "border-border bg-card text-muted-foreground"
                )}
              >
                {isComplete ? <Check size={14} strokeWidth={3} /> : index + 1}
              </div>
              <span
                className={cn(
                  "whitespace-nowrap text-xs font-medium",
                  isActive ? "text-brand-gold-deep dark:text-brand-gold" : "text-muted-foreground"
                )}
              >
                {t(`stages.${stage.label}`)}
              </span>
            </div>

            {index < stages.length - 1 && (
              <div
                className={cn(
                  "mx-2 h-0.5 flex-1 rounded-full transition-colors",
                  isComplete ? "bg-brand-violet" : "bg-border"
                )}
                style={{ marginBottom: 20 }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
