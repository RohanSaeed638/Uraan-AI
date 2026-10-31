"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Compass, Plus } from "lucide-react";

import { listAdminCareers } from "@/lib/api/admin";

import EmptyState from "@/components/shared/EmptyState";
import Pill from "@/components/shared/Pill";
import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function AdminCareersPage() {
  const t = useTranslations("admin.careers");
  const query = useQuery({ queryKey: ["admin", "careers"], queryFn: listAdminCareers });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">{t("intro")}</p>
        <Link href="/admin/careers/new" className={buttonVariants({ className: "gap-2" })}>
          <Plus size={16} /> {t("new")}
        </Link>
      </div>

      {query.isError ? (
        <EmptyState icon={Compass} title={t("failed")} />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b text-xs text-muted-foreground">
                <th className="p-3 text-start font-medium">{t("name")}</th>
                <th className="p-3 text-start font-medium">{t("category")}</th>
                <th className="p-3 text-start font-medium">{t("level")}</th>
                <th className="p-3 text-end font-medium">{t("skills")}</th>
                <th className="p-3 text-end font-medium">{t("resources")}</th>
                <th className="p-3 text-start font-medium">{t("status")}</th>
              </tr>
            </thead>
            <tbody>
              {(query.data ?? []).map((c) => (
                <tr key={c.id} className="border-b last:border-0 hover:bg-muted/40">
                  <td className="p-3">
                    <Link href={`/admin/careers/${c.id}`} className="font-medium hover:underline">
                      {c.name}
                    </Link>
                    <span className="ms-2 text-xs text-muted-foreground">{c.slug}</span>
                  </td>
                  <td className="p-3 text-muted-foreground">{c.category ?? "-"}</td>
                  <td className="p-3 text-muted-foreground">{c.difficulty ?? "-"}</td>
                  <td className="p-3 text-end">{c.skills}</td>
                  <td className="p-3 text-end">{c.resources}</td>
                  <td className="p-3">
                    <Pill tone={c.is_active ? "gold" : "soft"}>{c.is_active ? t("active") : t("off")}</Pill>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
