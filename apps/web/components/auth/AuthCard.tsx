import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export default function AuthCard({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn("w-full max-w-md p-8 sm:p-9", className)}>
      {children}
    </Card>
  );
}
