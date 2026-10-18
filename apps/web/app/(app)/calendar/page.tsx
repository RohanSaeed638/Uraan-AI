import { getCalendarSchedule, getCalendarToken } from "@/lib/server/data";

import CalendarClient from "./CalendarClient";

export default async function CalendarPage() {
  const [schedule, subscription] = await Promise.all([
    getCalendarSchedule(),
    getCalendarToken(),
  ]);

  return (
    <CalendarClient
      schedule={schedule}
      initialToken={subscription?.token ?? null}
      apiUrl={process.env.NEXT_PUBLIC_API_URL ?? ""}
    />
  );
}
