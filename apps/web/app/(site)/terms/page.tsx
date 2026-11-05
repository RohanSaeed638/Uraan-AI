import type { Metadata } from "next";

import ContactLine from "@/components/site/ContactLine";
import LegalPage, { type LegalSection } from "@/components/site/LegalPage";

export const metadata: Metadata = {
  title: "Terms of Service",
  description: "The rules for using Uraan AI.",
};

const sections: LegalSection[] = [
  {
    title: "Agreeing to these terms",
    body: [
      "By creating an account or using Uraan AI you agree to these Terms and to our Privacy Policy. If you do not agree, please do not use the service.",
    ],
  },
  {
    title: "What the service is",
    body: [
      "Uraan AI helps you explore careers, build a personalised learning roadmap and practise with AI tools. It is currently in beta and free to use. Features may change, be limited or be removed, and the service may be unavailable from time to time.",
    ],
  },
  {
    title: "Your account",
    body: [
      [
        "Give accurate information and keep it up to date.",
        "Keep your password private. You are responsible for what happens under your account.",
        "One account per person. Tell us promptly if you think someone else has used yours.",
        "You must be 13 or older. If you are under 18, use the service with a parent or guardian's knowledge.",
      ],
    ],
  },
  {
    title: "Using the service fairly",
    body: [
      "Please do not:",
      [
        "break the law, or use the service to harm, harass or deceive anyone;",
        "put in other people's private information, or anything you do not have the right to share;",
        "try to get around limits, access other learners' data, probe or attack the service, or overload it;",
        "copy the service's content in bulk, or use automated tools to collect it;",
        "use AI features to create content that is abusive, hateful, sexual involving minors, or otherwise harmful.",
      ],
      "We apply rate limits to keep the service fair for everyone. We may suspend or remove accounts that break these rules.",
    ],
  },
  {
    title: "AI-generated content",
    body: [
      "Roadmaps, lessons, quizzes, mentor replies, interview feedback, resumes and similar content are produced by AI. It can contain mistakes. It is learning support, not professional, legal, financial or career advice, and we do not promise any particular result, such as getting a job.",
      "Salary figures and other market information are rough guides only. Please check important facts yourself.",
    ],
  },
  {
    title: "Your content",
    body: [
      "You keep ownership of what you create or submit (for example your chat messages, documents and portfolio). You give us permission to store it, process it and send it to our AI and email providers as needed to run the features you use, as described in the Privacy Policy.",
      "If you publish your portfolio, you are responsible for what is on it, and anyone with the address can see it.",
    ],
  },
  {
    title: "Our content and other people's",
    body: [
      "The service, its design, and the careers catalogue are ours or our licensors'. You may use them for your own learning, but not copy or resell them.",
      "Roadmaps and lessons often link to courses, videos and tools run by other people. We do not control them, and their own terms apply when you use them.",
    ],
  },
  {
    title: "Ending your use",
    body: [
      "You can stop using the service at any time, and you can ask us to delete your account (see the Privacy Policy). We may suspend or end access if you break these terms or if we have to stop offering the service. Where reasonable, we will give you notice and a chance to download your data first.",
    ],
  },
  {
    title: "No guarantees, and limits on our responsibility",
    body: [
      "The service is provided \"as is\" and \"as available\". To the extent the law allows, we are not responsible for indirect or consequential losses, for lost opportunities, or for decisions you make based on AI-generated content. Nothing here limits responsibility that cannot legally be limited.",
    ],
  },
  {
    title: "Changes and the law",
    body: [
      "We may update these Terms. If a change matters, we will tell you in the app or by email before it takes effect, and continuing to use the service afterwards means you accept it. These Terms are governed by the laws of Pakistan.",
    ],
  },
  {
    title: "Contact",
    body: [
      <p key="c">
        Questions about these Terms: <ContactLine />.
      </p>,
    ],
  },
];

export default function TermsPage() {
  return (
    <LegalPage
      title="Terms of Service"
      intro="These are the rules for using Uraan AI. We have tried to keep them short and clear."
      sections={sections}
    />
  );
}
