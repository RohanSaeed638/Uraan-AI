export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="min-h-screen bg-gradient-to-br from-violet-600 via-purple-600 to-slate-900 flex items-center justify-center p-6">
      {children}
    </main>
  );
}