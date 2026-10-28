import { useTranslations } from "next-intl";
import { Compass } from "lucide-react";
import GenerateRoadmapButton from "./GenerateRoadmapButton";

export default function EmptyState() {
  const t = useTranslations("roadmaps");

  return (
    <div className="flex flex-col items-center rounded-3xl border border-dashed border-border p-14 text-center">
      <span className="flex size-14 items-center justify-center rounded-full bg-brand-violet/10">
        <Compass className="size-6 text-brand-violet" />
      </span>
      <h2 className="font-heading mt-5 text-2xl font-bold">
        {t("emptyTitle")}
      </h2>
      <p className="mt-2 max-w-sm text-muted-foreground">
        {t("emptyText")}
      </p>
      <div className="mt-7">
        <GenerateRoadmapButton />
      </div>
    </div>
  );
}
