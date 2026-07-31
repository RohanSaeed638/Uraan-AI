"use client";
import Image from "next/image";
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
    title: "Roadmaps",
    href: "/roadmaps",
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
    <aside className="sticky top-0 h-screen w-72 shrink-0 border-r bg-card p-6">
      <h1 className="text-2xl font-bold text-violet-600">
        {/* <Image src="/logo-whitebg.png" alt="Uraan AI" width={32} height={32} className="w-32 h-32" /> */}
        <a href="/">
          <img src="/logo-whitebg.png" alt="Uraan AI" width={64} height={42} className="w-64 h-42" />
        </a>
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