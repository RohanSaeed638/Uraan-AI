import { API_BASE } from "@/lib/api-base";
import { getCalendarSchedule, getCalendarToken } from "@/lib/server/data";

import PlannerClient from "@/components/planner/PlannerClient";

export default async function CalendarPage() {
  const [schedule, subscription] = await Promise.all([
    getCalendarSchedule(),
    getCalendarToken(),
  ]);

  return (
    <PlannerClient
      initial={schedule}
      initialToken={subscription?.token ?? null}
      apiUrl={API_BASE}
    />
  );
}
