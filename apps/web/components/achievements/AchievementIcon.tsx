import { createElement } from "react";
import {
  Award,
  BookOpen,
  Bot,
  Briefcase,
  CheckCircle2,
  ClipboardCheck,
  Clock,
  FileText,
  Flag,
  Flame,
  FolderKanban,
  Footprints,
  Hammer,
  Hourglass,
  Library,
  LucideIcon,
  Medal,
  Mic,
  Swords,
  Target,
  Zap,
} from "lucide-react";

// Icon names come from apps/api/app/core/achievement_catalog.py.
const ICONS: Record<string, LucideIcon> = {
  Award,
  BookOpen,
  Bot,
  Briefcase,
  CheckCircle2,
  ClipboardCheck,
  Clock,
  FileText,
  Flag,
  Flame,
  FolderKanban,
  Footprints,
  Hammer,
  Hourglass,
  Library,
  Mic,
  Swords,
  Target,
  Zap,
};

export default function AchievementIcon({
  name,
  size = 20,
}: {
  name: string;
  size?: number;
}) {
  return createElement(ICONS[name] ?? Medal, { size });
}
