import Link from "next/link";

import { CONTACT_EMAIL } from "@/lib/site";

/** The contact address as a link, or a pointer to the Contact page if none is set. */
export default function ContactLine() {
  if (!CONTACT_EMAIL) {
    return (
      <Link href="/contact" className="font-medium text-violet-700 underline dark:text-brand-violet-light">
        the Contact page
      </Link>
    );
  }

  return (
    <a href={`mailto:${CONTACT_EMAIL}`} className="font-medium text-violet-700 underline dark:text-brand-violet-light">
      {CONTACT_EMAIL}
    </a>
  );
}
