export default function RoseLogo({ size = 24, className = "", glow = true }) {
  const filter = glow
    ? "drop-shadow(0 0 10px rgba(var(--logo-glow-primary-rgb, 255, 77, 157), 0.55)) drop-shadow(0 0 16px rgba(var(--logo-glow-secondary-rgb, 255, 214, 231), 0.35))"
    : "none";

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      className={className}
      style={{ filter }}
      role="img"
      aria-label="Rose logo"
    >
      <defs>
        <linearGradient id="roseGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--accent-purple)" />
          <stop offset="100%" stopColor="var(--logo-fill, #ff4d9d)" />
        </linearGradient>
      </defs>
      {/* Gül yaprakları - spiral şeklinde */}
      <g fill="url(#roseGrad)" opacity="0.95">
        {/* Merkez */}
        <ellipse cx="32" cy="24" rx="4" ry="5" />
        {/* İç yapraklar */}
        <path d="M28 22c-3-2-6 0-7 4s1 7 4 8c-1-4 0-8 3-12Z" />
        <path d="M36 22c3-2 6 0 7 4s-1 7-4 8c1-4 0-8-3-12Z" />
        {/* Orta yapraklar */}
        <path d="M24 26c-5-1-9 3-9 8s3 8 7 8c-2-5-1-11 2-16Z" />
        <path d="M40 26c5-1 9 3 9 8s-3 8-7 8c2-5 1-11-2-16Z" />
        {/* Dış yapraklar */}
        <path d="M20 32c-4 2-6 7-4 12s6 7 10 5c-4-4-6-10-6-17Z" />
        <path d="M44 32c4 2 6 7 4 12s-6 7-10 5c4-4 6-10 6-17Z" />
      </g>
      {/* Gövde */}
      <path
        d="M32 42v18"
        stroke="var(--accent-green, #7cf4c9)"
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
      />
      {/* Yaprak */}
      <path
        d="M32 50c-4-2-8 0-10 4 4 0 8-1 10-4Z"
        fill="var(--accent-green, #7cf4c9)"
        opacity="0.85"
      />
    </svg>
  );
}
