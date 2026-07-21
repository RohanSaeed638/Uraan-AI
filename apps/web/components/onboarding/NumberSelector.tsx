"use client";

import { Button } from "@/components/ui/button";

interface Props {
  value: number;
  values: number[];
  suffix?: string;
  onChange: (value: number) => void;
}

export default function NumberSelector({
  value,
  values,
  suffix = "",
  onChange,
}: Props) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {values.map((item) => (
        <Button
          key={item}
          type="button"
          variant={
            value === item
              ? "default"
              : "outline"
          }
          onClick={() => onChange(item)}
        >
          {item}
          {suffix}
        </Button>
      ))}
    </div>
  );
}