import { getDocuments } from "@/lib/server/data";

import ResumeClient from "./ResumeClient";

export default async function ResumePage() {
  const data = await getDocuments();

  return <ResumeClient initialDocuments={data?.documents ?? []} />;
}
