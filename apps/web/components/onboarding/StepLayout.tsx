"use client";

import { ReactNode } from "react";

interface Props {
  children: ReactNode;
}

export default function StepLayout({
  children,
}: Props) {
  return (
    <div className="mx-auto flex min-h-[70vh] max-w-3xl items-center justify-center">
      {children}
    </div>
  );
}