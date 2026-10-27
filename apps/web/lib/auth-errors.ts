/** Keys of `auth.errors` for the Supabase messages learners meet most. */
export function authErrorKey(message: string): string | null {
  const text = message.toLowerCase();

  if (text.includes("invalid login credentials")) return "invalidCredentials";
  if (text.includes("email not confirmed")) return "emailNotConfirmed";
  if (text.includes("already registered") || text.includes("already been registered"))
    return "alreadyRegistered";
  if (text.includes("rate limit") || text.includes("too many")) return "rateLimited";

  return null;
}
