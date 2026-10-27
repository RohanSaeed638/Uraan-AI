import UnsubscribeClient from "./UnsubscribeClient";

/** Where the unsubscribe link in an email lands. Public: the link is signed. */
export default async function UnsubscribePage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>;
}) {
  const { token } = await searchParams;

  return <UnsubscribeClient token={token ?? ""} />;
}
