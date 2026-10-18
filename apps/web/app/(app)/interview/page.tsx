import { getInterviews } from "@/lib/server/data";

import InterviewHome from "./InterviewHome";

export default async function InterviewPage() {
  const data = await getInterviews();

  return <InterviewHome initialSessions={data?.sessions ?? []} />;
}
