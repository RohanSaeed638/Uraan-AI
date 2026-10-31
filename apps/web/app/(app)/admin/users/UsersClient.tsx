"use client";

import { useState } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { listAdminUsers, setUserRole } from "@/lib/api/admin";
import { apiErrorMessage } from "@/lib/profile-options";

import EmptyState from "@/components/shared/EmptyState";
import SearchField from "@/components/shared/SearchField";
import NativeSelect from "@/components/shared/NativeSelect";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Users } from "lucide-react";

const PAGE = 25;

export default function UsersClient() {
  const t = useTranslations("admin.users");
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);

  const query = useQuery({
    queryKey: ["admin", "users", search, page],
    queryFn: () => listAdminUsers({ search: search || undefined, limit: PAGE, offset: page * PAGE }),
    placeholderData: keepPreviousData,
  });

  const role = useMutation({
    mutationFn: ({ id, role }: { id: string; role: "user" | "admin" }) => setUserRole(id, role),
    onSuccess: () => {
      toast.success(t("roleSaved"));
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
    onError: (error) => toast.error(apiErrorMessage(error, t("roleFailed"))),
  });

  const total = query.data?.total ?? 0;
  const last = Math.max(0, Math.ceil(total / PAGE) - 1);

  return (
    <div className="space-y-4">
      <SearchField
        value={search}
        onChange={(value) => {
          setSearch(value);
          setPage(0);
        }}
        placeholder={t("search")}
        className="max-w-md"
      />

      {query.isError ? (
        <EmptyState icon={Users} title={t("failed")} />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full min-w-[760px] text-sm">
            <thead>
              <tr className="border-b text-xs text-muted-foreground">
                <th className="p-3 text-start font-medium">{t("name")}</th>
                <th className="p-3 text-start font-medium">{t("email")}</th>
                <th className="p-3 text-start font-medium">{t("career")}</th>
                <th className="p-3 text-end font-medium">{t("xp")}</th>
                <th className="p-3 text-end font-medium">{t("roadmaps")}</th>
                <th className="p-3 text-start font-medium">{t("joined")}</th>
                <th className="p-3 text-start font-medium">{t("role")}</th>
              </tr>
            </thead>
            <tbody>
              {(query.data?.items ?? []).map((u) => (
                <tr key={u.id} className="border-b last:border-0">
                  <td className="p-3 font-medium">
                    {u.name}
                    <span className="ms-2 text-xs text-muted-foreground">{u.language}</span>
                  </td>
                  <td className="p-3 text-muted-foreground">{u.email ?? "-"}</td>
                  <td className="p-3 text-muted-foreground">{u.career_slug ?? "-"}</td>
                  <td className="p-3 text-end">{u.xp}</td>
                  <td className="p-3 text-end">{u.roadmaps}</td>
                  <td className="p-3 text-muted-foreground">{u.created_at.slice(0, 10)}</td>
                  <td className="p-3">
                    <NativeSelect
                      aria-label={t("roleOf", { name: u.name })}
                      value={u.role}
                      active={u.role === "admin"}
                      disabled={role.isPending}
                      onChange={(e) => role.mutate({ id: u.id, role: e.target.value as "user" | "admin" })}
                    >
                      <option value="user">{t("user")}</option>
                      <option value="admin">{t("admin")}</option>
                    </NativeSelect>
                  </td>
                </tr>
              ))}
              {query.data && query.data.items.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-muted-foreground">
                    {t("none")}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </Card>
      )}

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>{t("total", { count: total })}</span>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage(page - 1)}>
            {t("previous")}
          </Button>
          <Button variant="outline" size="sm" disabled={page >= last} onClick={() => setPage(page + 1)}>
            {t("next")}
          </Button>
        </div>
      </div>
    </div>
  );
}
