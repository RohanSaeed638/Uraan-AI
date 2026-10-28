import { getCareersServer } from "@/lib/server/data";

import CareersClient from "./CareersClient";

export default async function CareersPage() {
  const list = await getCareersServer();

  return <CareersClient initial={list} />;
}
