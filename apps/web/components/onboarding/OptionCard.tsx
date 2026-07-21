"use client";

import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface OptionCardProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  selected: boolean;
  onClick: () => void;
}

export default function OptionCard({
  title,
  description,
  icon,
  selected,
  onClick,
}: OptionCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "w-full rounded-xl border p-5 transition-all text-left",
        "hover:shadow-lg hover:-translate-y-1",
        selected
          ? "border-purple-600 bg-purple-50 ring-2 ring-purple-400"
          : "border-gray-200 bg-white"
      )}
    >
      {icon && (
        <div className="mb-4 text-purple-600">
          {icon}
        </div>
      )}

      <h3 className="font-semibold text-lg">
        {title}
      </h3>

      {description && (
        <p className="mt-2 text-sm text-gray-500">
          {description}
        </p>
      )}
    </button>
  );
}