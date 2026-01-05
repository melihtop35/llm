export default function NoirLogo({ size = 24, className = "", glow = true }) {
  const filter = glow
    ? "drop-shadow(0 0 10px rgba(var(--logo-glow-primary-rgb, 61, 181, 255), 0.55)) drop-shadow(0 0 16px rgba(var(--logo-glow-secondary-rgb, 35, 255, 194), 0.35))"
    : "none";

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      className={className}
      style={{ filter }}
      role="img"
      aria-label="Theme logo"
    >
      <defs>
        <linearGradient id="noirGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="var(--accent-cyan)" />
          <stop offset="1" stopColor="var(--accent-purple)" />
        </linearGradient>
      </defs>

      <path
        d="M32 4 56 18v28L32 60 8 46V18L32 4Z"
        fill="none"
        stroke="url(#noirGrad)"
        strokeWidth="3"
      />
      <path
        d="M20 44V20l24 24V20"
        fill="none"
        stroke="var(--logo-fill, currentColor)"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
