import type { Metadata } from "next";

import ContactLine from "@/components/site/ContactLine";
import LegalPage, { type LegalSection } from "@/components/site/LegalPage";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "What Uraan AI collects, why, who helps us run it, and the choices you have.",
};

const sections: LegalSection[] = [
  {
    title: "Who we are",
    body: [
      "Uraan AI (\"we\", \"us\") is a learning platform that helps people choose a career, follow a personalised roadmap and practise with an AI mentor. This policy explains what information we handle when you use it and what you can do about it.",
      <p key="c">
        Questions or requests about your information: <ContactLine />.
      </p>,
    ],
  },
  {
    title: "What we collect",
    body: [
      "Account details: your name and email address. Your password is handled by our sign-in provider; we never see it. If you sign in with Google or GitHub, we receive the name and email that account shares with us.",
      "Your learning profile: the answers you give when you start (such as career goal, skill level, study time, education, device and preferred study hours) and what you change later.",
      "Your activity: roadmaps and lessons you create, what you complete, XP, streaks, achievements, quiz answers, mock interview answers and scores, and your planner changes.",
      "What you write or send us: messages to the AI mentor, details you give for a resume or cover letter, portfolio text and project links, and code or links you submit for review.",
      "Technical information: your network address (used to limit abuse), basic browser details, and error reports when something breaks. Reports are scrubbed of names, emails and text before they are stored.",
      "Optional product statistics: counts of actions such as \"lesson completed\", linked to a random profile identifier, never to your name, email or what you wrote. These are collected only when the service is configured with an analytics provider.",
    ],
  },
  {
    title: "How we use it",
    body: [
      [
        "To run the service: build your roadmap and lessons, track progress and show your dashboard.",
        "To personalise: fit plans and explanations to your level, language, device and available time.",
        "To keep you on track: in-app notifications, and email or browser push reminders if you turn them on.",
        "To keep the service safe and working: rate limits, abuse prevention, error fixing and security.",
        "To improve it: understanding which features are used and where things fail.",
      ],
      "We do not sell your information and we do not show advertising.",
    ],
  },
  {
    title: "AI features",
    body: [
      "Roadmaps, lessons, quizzes, mentor replies, interview practice, resume drafts and similar features are written by AI models run by outside providers (currently OpenAI, Google and Anthropic, depending on availability). To produce an answer we send the provider the relevant parts of your profile and whatever you ask or submit, such as a chat message or code to review. We send only what the feature needs.",
      "The providers process this under their own terms. Please do not put sensitive information (such as identity numbers, financial details or other people's private data) into the mentor, resume or review features.",
      "AI output can be wrong or out of date. Check anything important before you rely on it.",
    ],
  },
  {
    title: "What other people can see",
    body: [
      [
        "Public portfolio: nothing is public until you publish it. A published portfolio shows the name, headline, bio and the projects you mark visible, at the address you choose. You can unpublish at any time.",
        "Leaderboard: your name and XP appear on the leaderboard unless you switch that off in Settings.",
        "Everything else (roadmaps, chats, documents, interview answers) is private to your account and to the administrators who operate the service.",
      ],
    ],
  },
  {
    title: "Who helps us run it",
    body: [
      "We use these kinds of service providers, who handle information only to provide their service to us:",
      [
        "Supabase: our database and sign-in.",
        "AI providers: described above.",
        "Resend: sending email (reminders and account emails), if enabled.",
        "Our hosting providers: serving the website and the API.",
        "Sentry and PostHog: error reports and product statistics, if enabled.",
      ],
      "Some of these providers are located in or process data in other countries, so your information may be stored or handled outside Pakistan. We may also share information when the law requires it.",
    ],
  },
  {
    title: "Cookies and similar storage",
    body: [
      "We use cookies and browser storage that the site needs to work: to keep you signed in, and to remember your language, theme and wording choices. We do not use advertising or cross-site tracking cookies.",
    ],
  },
  {
    title: "How long we keep it",
    body: [
      "We keep your information while your account exists. Backups may hold deleted data for a short time before they are overwritten. Error reports and logs are kept only as long as needed to find and fix problems.",
    ],
  },
  {
    title: "Your choices",
    body: [
      [
        "See and correct: your Profile page shows what you told us and lets you change it.",
        "Download: Settings > Data lets you download a copy of your information.",
        "Notifications: turn email and reminders off in Settings, or use the unsubscribe link in any email.",
        "Delete: ask us to delete your account and its data using the contact details above. We will confirm your identity and normally complete the request within 30 days.",
      ],
    ],
  },
  {
    title: "Security",
    body: [
      "We protect data with encrypted connections, access controls on every table in the database, limits on how fast requests can be made, and separation between learners' data. No online service can promise perfect security, so please use a strong, unique password.",
    ],
  },
  {
    title: "Young learners",
    body: [
      "Uraan AI is for learners aged 13 and over. If you are under 18, please use it with the knowledge of a parent or guardian. If you believe a child has given us information without permission, contact us and we will remove it.",
    ],
  },
  {
    title: "Changes to this policy",
    body: [
      "If we change this policy in a way that matters, we will tell you in the app or by email before the change takes effect. The date at the top shows when it last changed.",
    ],
  },
];

export default function PrivacyPage() {
  return (
    <LegalPage
      title="Privacy Policy"
      intro="We want you to know exactly what happens to your information. This page is written in plain English; if a translated version differs, the English one applies."
      sections={sections}
    />
  );
}
