import { getTranslations } from "next-intl/server";

import { createClient } from "@/lib/supabase/server";
import PageHeader from "@/components/shared/PageHeader";

import RoadmapList from "./RoadmapList";
import EmptyState from "./EmptyState";
import GenerateRoadmapButton from "./GenerateRoadmapButton";
import { RoadmapSummary } from "@/types/roadmap";

export default async function RoadmapPage({
  searchParams,
}: {
  searchParams: Promise<{ career?: string }>;
}) {
  const { career } = await searchParams;
  const t = await getTranslations("roadmaps");

  const supabase = await createClient();

  const {
    data: { session },
  } = await supabase.auth.getSession();

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/roadmaps`,
    {
      headers: { Authorization: `Bearer ${session?.access_token}` },
      cache: "no-store",
    }
  );
  const data = await response.json();
  const roadmaps: RoadmapSummary[] = Array.isArray(data) ? data : [];

  return (
    <main className="mx-auto max-w-6xl">
      <PageHeader
        className="mb-6"
        title={t("title")}
        subtitle={t("subtitle")}
        actions={<GenerateRoadmapButton defaultCareer={career} />}
      />

      {roadmaps.length === 0 ? (
        <EmptyState />
      ) : (
        <RoadmapList roadmaps={roadmaps} />
      )}
    </main>
  );
}
