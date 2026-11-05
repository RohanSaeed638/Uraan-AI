import ResourcesClient from "./ResourcesClient";

export default async function ResourcesPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string | string[] }>;
}) {
  const { q } = await searchParams;

  // A link from the top-bar search arrives as /resources?q=<title>.
  return <ResourcesClient initialQuery={typeof q === "string" ? q.slice(0, 100) : ""} />;
}
