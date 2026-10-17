export default function CheckIllustration({ size = 160 }: { size?: number }) {
  return (
    <svg viewBox="0 0 200 200" width={size} height={size} aria-hidden>
      <defs>
        <linearGradient id="check-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#a78bfa" />
          <stop offset="1" stopColor="#7c3aed" />
        </linearGradient>
      </defs>
      <circle cx="100" cy="100" r="76" fill="url(#check-grad)" opacity="0.15" />
      <circle cx="100" cy="100" r="54" fill="url(#check-grad)" />
      <path
        d="M78 101 L93 116 L124 82"
        stroke="white"
        strokeWidth="9"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );
}
