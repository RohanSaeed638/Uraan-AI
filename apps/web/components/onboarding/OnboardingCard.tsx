import { ReactNode } from "react";

interface Props {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

export default function OnboardingCard({
  title,
  subtitle,
  children,
}: Props) {

  return (

    <div className="mx-auto w-full max-w-3xl rounded-3xl border bg-white p-10 shadow-sm">

      <h1 className="text-3xl font-bold">

        {title}

      </h1>

      {subtitle && (

        <p className="mt-2 text-gray-500">

          {subtitle}

        </p>

      )}

      <div className="mt-10">

        {children}

      </div>

    </div>

  );
}