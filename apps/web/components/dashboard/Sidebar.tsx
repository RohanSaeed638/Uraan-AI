"use client";

import Link from "next/link";
import {
  Home,
  Target,
  Calendar,
  Briefcase,
  Bot,
  User,
  Settings,
} from "lucide-react";

const items = [
  {
    title: "Dashboard",
    href: "/dashboard",
    icon: Home,
  },
  {
    title: "Roadmap",
    href: "/roadmap",
    icon: Target,
  },
  {
    title: "Careers",
    href: "/careers",
    icon: Briefcase,
  },
  {
    title: "Schedule",
    href: "/schedule",
    icon: Calendar,
  },
  {
    title: "AI Mentor",
    href: "/mentor",
    icon: Bot,
  },
  {
    title: "Profile",
    href: "/profile",
    icon: User,
  },
  {
    title: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

export default function Sidebar() {
  return (
    <aside className="w-72 border-r bg-card p-6">
      <h1 className="text-2xl font-bold text-violet-600">
        Uraan AI
      </h1>

      <nav className="mt-10 space-y-2">
        {items.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="flex items-center gap-3 rounded-lg p-3 hover:bg-muted transition"
          >
            <item.icon size={18} />

            {item.title}
          </Link>
        ))}
      </nav>
    </aside>
  );
}