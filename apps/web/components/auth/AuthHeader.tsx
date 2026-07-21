export default function AuthHeader({
  title,
  subtitle,
}: {
  title: string;
  subtitle: string;
}) {
  return (
    <div className="space-y-2 mb-8 text-center">
      <h1 className="text-3xl font-bold">
        {title}
      </h1>

      <p className="text-muted-foreground">
        {subtitle}
      </p>
    </div>
  );
}