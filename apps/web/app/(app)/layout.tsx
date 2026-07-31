import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

import Sidebar from "@/components/dashboard/Sidebar";
import Navbar from "@/components/dashboard/Navbar";
import ReactQueryProvider from "@/providers/ReactQueryProvider";
export default async function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <div className="h-screen flex overflow-hidden bg-background">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="sticky top-0 z-20 bg-background border-b">
          <Navbar user={user} />
        </div>
        <main className="flex-1 overflow-y-auto p-8">
          <ReactQueryProvider>
            {children}
          </ReactQueryProvider>
        </main>
      </div>
    </div>
  );
}