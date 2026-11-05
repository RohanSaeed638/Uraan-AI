import { getDocuments } from "@/lib/server/data";

import ResumeClient from "./ResumeClient";

export default async function ResumePage({
  searchParams,
}: {
  searchParams: Promise<{ d?: string | string[] }>;
}) {
  const [data, { d }] = await Promise.all([getDocuments(), searchParams]);

  // A link from the top-bar search arrives as /resume?d=<document id>.
  return <ResumeClient initialDocuments={data?.documents ?? []} openId={typeof d === "string" ? d : null} />;
}
