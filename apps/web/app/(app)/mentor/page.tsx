import Link from "next/link";
import { Bot } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { getUserSettings } from "@/lib/server/data";

import { buttonVariants } from "@/components/ui/button";

import MentorClient from "./MentorClient";

export default async function MentorPage() {
  const t = await getTranslations("mentorChat");
  const settings = await getUserSettings();

  // Only an explicit "off" blocks the mentor; unknown settings keep it on.
  if (settings && !settings.ai_mentor_enabled) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center py-16 text-center">
        <span className="flex size-16 items-center justify-center rounded-full bg-muted">
          <Bot className="size-7 text-muted-foreground" />
        </span>
        <h1 className="font-heading mt-6 text-2xl font-bold">
          {t("offTitle")}
        </h1>
        <p className="mt-2 text-muted-foreground">
          {t("offText")}
        </p>
        <Link
          href="/settings?tab=preferences"
          className={buttonVariants({ className: "mt-6" })}
        >
          {t("openSettings")}
        </Link>
      </div>
    );
  }

  return <MentorClient />;
}
