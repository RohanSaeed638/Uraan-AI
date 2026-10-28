import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";

export default function Logo({
  variant = "full",
  size = 32,
  href = "/",
  className,
}: {
  variant?: "full" | "icon";
  size?: number;
  href?: string | null;
  className?: string;
}) {
  const content =
    variant === "icon" ? (
      <Image
        src="/bird-icon.png"
        alt="Uraan AI"
        width={size}
        height={size}
        className={cn("object-contain", className)}
        style={{ width: size, height: "auto" }}
        priority
      />
    ) : (
      <span className={cn("flex items-center gap-2", className)}>
        <Image
          src="/bird-icon.png"
          alt=""
          aria-hidden
          width={size}
          height={size}
          className="object-contain"
          style={{ width: size, height: "auto" }}
          priority
        />
        <span
          className="font-heading font-bold tracking-wide text-foreground"
          style={{ fontSize: size * 0.6 }}
        >
          Uraan <span className="text-brand-gold">AI</span>
        </span>
      </span>
    );

  if (!href) return content;

  return (
    <Link href={href} className="inline-flex items-center">
      {content}
    </Link>
  );
}
