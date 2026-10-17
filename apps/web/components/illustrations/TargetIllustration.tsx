export default function TargetIllustration({ size = 160 }: { size?: number }) {
  return (
    <svg
      viewBox="0 0 200 200"
      width={size}
      height={size}
      aria-hidden
    >
      <defs>
        <linearGradient id="target-ring" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#a78bfa" />
          <stop offset="1" stopColor="#7c3aed" />
        </linearGradient>
      </defs>
      <circle
        cx="100"
        cy="100"
        r="76"
        fill="none"
        stroke="url(#target-ring)"
        strokeWidth="14"
        opacity="0.25"
      />
      <circle
        cx="100"
        cy="100"
        r="54"
        fill="none"
        stroke="url(#target-ring)"
        strokeWidth="14"
        opacity="0.5"
      />
      <circle
        cx="100"
        cy="100"
        r="32"
        fill="none"
        stroke="url(#target-ring)"
        strokeWidth="14"
        opacity="0.8"
      />
      <circle cx="100" cy="100" r="11" fill="#f5a83c" />
      <path
        d="M152 48 L104 96"
        stroke="#ffcf7a"
        strokeWidth="5"
        strokeLinecap="round"
      />
      <path d="M104 96 L120 90 L110 106 Z" fill="#f5a83c" />
      <path d="M152 48 L162 60 L140 58 Z" fill="#ffcf7a" />
      <path d="M152 48 L140 70 L144 50 Z" fill="#ffcf7a" />
    </svg>
  );
}
