/**
 * The landing page's backdrop: soft violet light from above, two slow glows (violet and
 * gold, the brand colours), a dot pattern that fades out towards the edges, and a dashed
 * "flight path" climbing across the hero ("Uraan" means flight). Pure CSS and SVG, no
 * images, and decorative only. Put it inside a `relative isolate` section.
 */
export default function HeroBackground() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      {/* light from above */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_90%_70%_at_50%_-10%,rgba(124,58,237,0.20),transparent_70%)] dark:bg-[radial-gradient(ellipse_90%_70%_at_50%_-10%,rgba(124,58,237,0.42),transparent_70%)]" />

      {/* two glows that drift slowly */}
      <div className="hero-float absolute -start-28 top-8 size-[28rem] rounded-full bg-violet-400/25 blur-3xl dark:bg-violet-600/30" />
      <div className="hero-float-slow absolute -end-24 top-44 size-[24rem] rounded-full bg-amber-300/30 blur-3xl dark:bg-amber-500/15" />
      <div className="hero-float-slow absolute start-1/3 top-72 size-[20rem] rounded-full bg-indigo-300/20 blur-3xl dark:bg-indigo-500/20" />

      {/* dots, brightest in the middle */}
      <div className="absolute inset-0 [background-image:radial-gradient(circle,rgba(91,33,182,0.30)_1px,transparent_1.6px)] [background-size:26px_26px] [mask-image:radial-gradient(ellipse_75%_65%_at_50%_30%,black,transparent)] dark:[background-image:radial-gradient(circle,rgba(196,181,253,0.26)_1px,transparent_1.6px)]" />

      {/* the flight path: rises from bottom-left to top-right, mirrored for right-to-left languages */}
      <svg
        viewBox="0 0 1200 560"
        preserveAspectRatio="none"
        className="absolute inset-0 size-full [mask-image:radial-gradient(ellipse_34%_30%_at_50%_42%,transparent_55%,black_100%)] rtl:-scale-x-100"
        fill="none"
      >
        <defs>
          <linearGradient id="flight" x1="0" y1="1" x2="1" y2="0">
            <stop offset="0%" stopColor="#7c3aed" stopOpacity="0" />
            <stop offset="35%" stopColor="#7c3aed" stopOpacity="0.55" />
            <stop offset="100%" stopColor="#f5a83c" stopOpacity="0.9" />
          </linearGradient>
        </defs>
        <path
          d="M-20 500 C 240 520, 330 210, 600 250 S 980 70, 1220 -10"
          stroke="url(#flight)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeDasharray="2 11"
          vectorEffect="non-scaling-stroke"
        />
        <g fill="#f5a83c" fillOpacity="0.9">
          <circle cx="905" cy="105" r="4" />
          <circle cx="1100" cy="30" r="3" />
        </g>
        <g fill="#7c3aed" fillOpacity="0.5">
          <circle cx="300" cy="360" r="4" />
        </g>
      </svg>

      {/* melt into the page below */}
      <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-b from-transparent to-background" />
    </div>
  );
}
