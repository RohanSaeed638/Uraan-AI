interface Props {
  title: string;
  subtitle?: string;
}

export default function SectionTitle({
  title,
  subtitle,
}: Props) {
  return (
    <div className="mb-8">
      <h1 className="text-3xl font-bold">
        {title}
      </h1>

      {subtitle && (
        <p className="mt-3 text-gray-500">
          {subtitle}
        </p>
      )}
    </div>
  );
}