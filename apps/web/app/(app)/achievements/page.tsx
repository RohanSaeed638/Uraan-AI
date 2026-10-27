import { getGamification } from "@/lib/server/data";

import AchievementsClient from "./AchievementsClient";

export default async function AchievementsPage() {
  const gamification = await getGamification();

  return <AchievementsClient gamification={gamification} />;
}
