import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages } from "next-intl/server";
import { Geist, Geist_Mono, Inter, Noto_Naskh_Arabic } from "next/font/google";
import "./globals.css";
import AuthProvider from "@/providers/AuthProvider";
import { cn } from "@/lib/utils";
import AppToaster from "@/components/shared/AppToaster";
import SkipLink from "@/components/shared/SkipLink";
import DirectionSync from "@/components/shared/DirectionSync";
import ErrorTranslator from "@/components/shared/ErrorTranslator";
import { isRtl } from "@/i18n/config";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

// Urdu script; loaded for every page but only used when the language is Urdu.
const urdu = Noto_Naskh_Arabic({
  subsets: ["arabic"],
  variable: "--font-urdu",
  display: "swap",
});

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: { default: "Uraan AI - AI-powered career growth", template: "%s | Uraan AI" },
  description:
    "Pick a career, get a personalised roadmap, and learn it step by step with an AI mentor. Free during beta.",
  icons: {
    icon: "/favicon.ico",
  },
  openGraph: {
    type: "website",
    siteName: "Uraan AI",
    title: "Uraan AI - AI-powered career growth",
    description: "Personalised roadmaps, practical lessons and an AI mentor for your next career.",
  },
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html
      lang={locale}
      dir={isRtl(locale) ? "rtl" : "ltr"}
      className={cn(
        "h-full",
        "dark",
        "antialiased",
        geistSans.variable,
        geistMono.variable,
        urdu.variable,
        "font-sans",
        inter.variable
      )}
      suppressHydrationWarning
    >
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                var stored = localStorage.getItem('uraan-theme');
                var dark = stored === 'light' ? false
                  : stored === 'system' ? window.matchMedia('(prefers-color-scheme: dark)').matches
                  : true;
                document.documentElement.classList.toggle('dark', dark);
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body className="min-h-full flex flex-col">
        <NextIntlClientProvider locale={locale} messages={messages}>
          <SkipLink />
          <ErrorTranslator />
          <DirectionSync>
            <AuthProvider>
              {children}
              <AppToaster />
            </AuthProvider>
          </DirectionSync>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
