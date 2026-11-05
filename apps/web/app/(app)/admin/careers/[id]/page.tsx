import { API_BASE } from "@/lib/api-base";
import { notFound } from "next/navigation";

import { createClient } from "@/lib/supabase/server";
import type { AdminCareer } from "@/lib/api/admin";

import CareerForm from "../CareerForm";

export default async function EditCareerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const res = await fetch(`${API_BASE}/admin/careers/${encodeURIComponent(id)}`, {
    headers: { Authorization: `Bearer ${session?.access_token}` },
    cache: "no-store",
  });

  if (!res.ok) notFound();

  return <CareerForm career={(await res.json()) as AdminCareer} />;
}
