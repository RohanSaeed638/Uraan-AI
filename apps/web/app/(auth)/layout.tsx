import AuthBrandPanel from "@/components/auth/AuthBrandPanel";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen bg-background">
      <AuthBrandPanel />
      <div className="flex flex-1 items-center justify-center p-6 sm:p-10">
        {children}
      </div>
    </main>
  );
}
