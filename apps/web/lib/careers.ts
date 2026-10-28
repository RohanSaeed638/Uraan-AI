import { createElement } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Brain,
  BarChart3,
  Briefcase,
  Camera,
  Clapperboard,
  Cloud,
  Layers,
  Layout,
  LucideIcon,
  Megaphone,
  Palette,
  PenTool,
  Server,
  ShieldCheck,
  Smartphone,
  Workflow,
} from "lucide-react";

import { useTranslations } from "next-intl";

import { listCareers } from "@/lib/api/careers";
import { careerText } from "@/lib/career-text";
import { careers as fallbackCareers } from "@/lib/constants/careers";
import { CareerSummary } from "@/types/api";

// Icon names come from data/careers.json; an unknown name falls back.
const ICONS: Record<string, LucideIcon> = {
  Server,
  Layout,
  Layers,
  Smartphone,
  Brain,
  BarChart3,
  ShieldCheck,
  Palette,
  Workflow,
  Cloud,
  Megaphone,
  PenTool,
  Clapperboard,
  Camera,
};

/** The icon element for a catalogue icon name (a generic one if unknown). */
export function careerIcon(name: string | null | undefined, size = 22) {
  return createElement((name && ICONS[name]) || Briefcase, { size });
}

/** "PKR 80k - 450k" from monthly salary figures. */
export function salaryRange(min?: number | null, max?: number | null): string | null {
  if (!min || !max) return null;

  const k = (n: number) => `${Math.round(n / 1000)}k`;

  return `PKR ${k(min)} - ${k(max)}`;
}

export const CAREERS_QUERY_KEY = ["careers", "catalogue"] as const;

/**
 * The live catalogue for pickers (onboarding, roadmap form). Falls back to the
 * built-in list if the API is unreachable, so the forms never go empty.
 */
export function useCareerOptions() {
  const ct = careerText(useTranslations("catalog"));
  const query = useQuery({
    queryKey: CAREERS_QUERY_KEY,
    queryFn: () => listCareers({}),
    staleTime: 5 * 60 * 1000,
  });

  const options: { value: string; label: string; description: string; icon: string | null }[] =
    query.data?.items.map((c: CareerSummary) => ({
      value: c.slug,
      label: ct.name(c.slug, c.name),
      description: ct.description(c.slug, c.description),
      icon: c.icon,
    })) ??
    fallbackCareers.map((c) => ({
      value: c.value,
      label: ct.name(c.value, c.label),
      description: ct.description(c.value, c.description),
      icon: null,
    }));

  return { options, loading: query.isLoading };
}
