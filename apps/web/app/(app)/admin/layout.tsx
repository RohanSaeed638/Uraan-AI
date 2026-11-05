import { notFound } from "next/navigation";
import { ServerCrash } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { getAdminMe } from "@/lib/server/data";

import EmptyState from "@/components/shared/EmptyState";
import PageHeader from "@/components/shared/PageHeader";

import AdminNav from "./AdminNav";

/** Everything under /admin. The API answers 403 to anyone who is not an admin,
 * and this shows them the same "not found" page as a address that does not
 * exist, so the portal is not advertised. */
export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const me = await getAdminMe();

  if (me === "forbidden") notFound();

  const t = await getTranslations("admin");

  if (me === "error") {
    return (
      <div className="mx-auto max-w-3xl">
        <EmptyState icon={ServerCrash} title={t("unavailable")} text={t("unavailableText")} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader title={t("title")} subtitle={t("subtitle", { name: me.name })} />
      <AdminNav />
      <div className="mt-6">{children}</div>
    </div>
  );
}
