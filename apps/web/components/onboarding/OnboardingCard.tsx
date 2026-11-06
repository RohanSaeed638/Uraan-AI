import { ReactNode } from "react";

import Illustration, { IllustrationName } from "@/components/illustrations/Illustration";
import { cn } from "@/lib/utils";

interface Props {
  title: string;
  subtitle?: string;
  /** The picture for this step, shown beside the form on wide screens and above it on phones. */
  art?: IllustrationName;
  children: ReactNode;
  className?: string;
}

export default function OnboardingCard({ title, subtitle, art, children, className }: Props) {
  return (
    <div
      className={cn(
        "relative mx-auto w-full max-w-5xl overflow-hidden rounded-3xl border border-border bg-card shadow-sm",
        art && "lg:grid lg:grid-cols-[1fr_300px]",
        className
      )}
    >
      <div className="min-w-0 p-6 sm:p-10">
        {art && (
          <div className="mb-4 flex justify-center lg:hidden">
            <Illustration name={art} size={120} />
          </div>
        )}

        <h1 className="font-heading text-2xl font-bold tracking-tight sm:text-3xl">{title}</h1>

        {subtitle && <p className="mt-2 max-w-xl text-muted-foreground">{subtitle}</p>}

        <div className="mt-8">{children}</div>
      </div>

      {art && (
        <aside
          aria-hidden
          className="relative hidden items-center justify-center border-s border-border bg-gradient-to-b from-brand-violet/10 via-brand-violet/5 to-transparent p-6 lg:flex"
        >
          <div className="absolute size-56 rounded-full bg-brand-violet/15 blur-3xl" />
          <Illustration name={art} size={240} className="float relative" priority />
        </aside>
      )}
    </div>
  );
}
