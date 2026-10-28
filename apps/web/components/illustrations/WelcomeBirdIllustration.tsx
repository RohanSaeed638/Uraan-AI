import Image from "next/image";
import { Sparkles, Star } from "lucide-react";

export default function WelcomeBirdIllustration({
  size = 140,
}: {
  size?: number;
}) {
  return (
    <div
      className="relative flex items-center justify-center"
      style={{ width: size * 1.7, height: size * 1.7 }}
      aria-hidden
    >
      <div
        className="absolute inset-0 rounded-full bg-brand-violet/20 blur-2xl"
        style={{ margin: size * 0.15 }}
      />
      <Star
        className="absolute start-2 top-4 text-brand-gold-light"
        size={size * 0.14}
        fill="currentColor"
      />
      <Star
        className="absolute bottom-6 start-6 text-brand-violet-light"
        size={size * 0.1}
        fill="currentColor"
      />
      <Sparkles
        className="absolute end-0 top-10 text-brand-gold-light"
        size={size * 0.16}
      />
      <Star
        className="absolute bottom-2 end-4 text-brand-gold-light"
        size={size * 0.12}
        fill="currentColor"
      />
      <Image
        src="/bird-icon.png"
        alt=""
        width={size}
        height={size}
        className="relative object-contain drop-shadow-[0_0_30px_rgba(124,58,237,0.5)]"
      />
    </div>
  );
}
