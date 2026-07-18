import { Card } from "@/components/ui/card";

export default function AuthCard({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Card className="w-full max-w-md p-8 shadow-2xl rounded-2xl">
      {children}
    </Card>
  );
}