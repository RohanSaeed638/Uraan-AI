import Illustration, { IllustrationName } from "@/components/illustrations/Illustration";

export default function AuthHeader({
  title,
  subtitle,
  art,
}: {
  title: string;
  subtitle: string;
  /** An optional picture shown above the title. */
  art?: IllustrationName;
}) {
  return (
    <div className="mb-7 space-y-1.5">
      {art && <Illustration name={art} size={140} className="mx-auto mb-3" />}
      <h1 className="font-heading text-2xl font-bold text-foreground">
        {title}
      </h1>
      <p className="text-sm text-muted-foreground">{subtitle}</p>
    </div>
  );
}
