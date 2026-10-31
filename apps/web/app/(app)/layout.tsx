import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

import Sidebar from "@/components/dashboard/Sidebar";
import Navbar from "@/components/dashboard/Navbar";
import BottomNav from "@/components/dashboard/BottomNav";
import ReactQueryProvider from "@/providers/ReactQueryProvider";
import ThemeSync from "@/components/shared/ThemeSync";
import ConfettiHost from "@/components/shared/ConfettiHost";
import AnnouncementBanner from "@/components/shared/AnnouncementBanner";
import { getProfileServer } from "@/lib/server/data";
import LocaleSync from "@/components/shared/LocaleSync";
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

  const isAdmin = (await getProfileServer())?.role === "admin";

  // The print: classes let a page print (or save as PDF) without the app
  // chrome or the fixed-height scroll container.
  return (
    <ReactQueryProvider>
      <ThemeSync />
      <LocaleSync />
      <ConfettiHost />
      <div className="h-screen flex overflow-hidden bg-background print:block print:h-auto print:overflow-visible">
        <Sidebar isAdmin={isAdmin} />

        <div className="flex min-w-0 flex-1 flex-col overflow-hidden print:block print:overflow-visible">
          <div className="sticky top-0 z-20 bg-background border-b print:hidden">
            <Navbar user={user} isAdmin={isAdmin} />
          </div>
          <AnnouncementBanner />
          <main id="main" tabIndex={-1} className="flex-1 overflow-y-auto outline-none p-4 sm:p-6 lg:p-8 print:overflow-visible print:p-0">
            {children}
          </main>
          <BottomNav />
        </div>
      </div>
    </ReactQueryProvider>
  );
}
