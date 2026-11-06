import Illustration, { IllustrationName } from "@/components/illustrations/Illustration";
import { cn } from "@/lib/utils";

/** The top of a page: a title with a gold marker, a line of help, and room on
 * the right for the page's main actions. */
export default function PageHeader({
  title,
  subtitle,
  actions,
  art,
  className,
}: {
  title: string;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  /** A small picture shown on the right on wider screens. */
  art?: IllustrationName;
  className?: string;
}) {
  return (
    <header
      className={cn(
        "mb-2 flex flex-wrap items-start justify-between gap-x-6 gap-y-4",
        className
      )}
    >
      <div className="min-w-0">
        <div className="flex items-center gap-3">
          <span aria-hidden className="h-8 w-1.5 shrink-0 rounded-full bg-brand-violet" />
          <h1 className="font-heading text-2xl font-bold sm:text-3xl">{title}</h1>
        </div>
        {subtitle && (
          <div className="mt-1.5 max-w-2xl ps-[18px] text-muted-foreground">{subtitle}</div>
        )}
      </div>

      {art && <Illustration name={art} size={96} className="ms-auto hidden sm:block" />}
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}
