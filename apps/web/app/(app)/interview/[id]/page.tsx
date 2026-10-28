import { notFound } from "next/navigation";

import { getInterview } from "@/lib/server/data";

import SessionClient from "./SessionClient";

export default async function InterviewSessionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const session = await getInterview(id);

  if (!session) notFound();

  return <SessionClient initial={session} />;
}
