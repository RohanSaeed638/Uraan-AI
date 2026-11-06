import { useTranslations } from "next-intl";
import Illustration from "@/components/illustrations/Illustration";
import GenerateRoadmapButton from "./GenerateRoadmapButton";

export default function EmptyState() {
  const t = useTranslations("roadmaps");

  return (
    <div className="flex flex-col items-center rounded-3xl border border-dashed border-border p-14 text-center">
      <Illustration name="path" size={190} className="float" />
      <h2 className="font-heading mt-4 text-2xl font-bold">
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
