export default function CyberpunkLogo({
  size = 24,
  className = "",
  glow = true,
}) {
  const filter = glow
    ? "drop-shadow(0 0 10px rgba(var(--logo-glow-primary-rgb, 252, 238, 10), 0.6)) drop-shadow(0 0 16px rgba(var(--logo-glow-secondary-rgb, 5, 217, 232), 0.4))"
    : "none";

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      className={className}
      style={{ filter }}
      role="img"
      aria-label="Cyberpunk theme logo"
    >
      <defs>
        <linearGradient id="cyberpunkGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#fcee0a" />
          <stop offset="50%" stopColor="#ff2a6d" />
          <stop offset="100%" stopColor="#05d9e8" />
        </linearGradient>
        <linearGradient id="cyberpunkGrad2" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0%" stopColor="#05d9e8" />
          <stop offset="100%" stopColor="#fcee0a" />
        </linearGradient>
      </defs>

      {/* Circuit board background pattern */}
      <rect
        x="8"
        y="8"
        width="48"
        height="48"
        rx="4"
        fill="none"
        stroke="url(#cyberpunkGrad2)"
        strokeWidth="1.5"
        opacity="0.5"
      />

      {/* Main "C" shape - Cyberpunk style */}
      <path
        d="M44 18H24c-3.3 0-6 2.7-6 6v16c0 3.3 2.7 6 6 6h20"
        fill="none"
        stroke="url(#cyberpunkGrad)"
        strokeWidth="4"
        strokeLinecap="square"
      />

      {/* Glitch lines */}
      <line
        x1="20"
        y1="28"
        x2="36"
        y2="28"
        stroke="var(--logo-fill, #fcee0a)"
        strokeWidth="2"
      />
      <line x1="24" y1="36" x2="40" y2="36" stroke="#05d9e8" strokeWidth="2" />

      {/* Tech dots */}
      <circle cx="46" cy="18" r="2.5" fill="var(--logo-fill, #fcee0a)" />
      <circle cx="46" cy="46" r="2.5" fill="#05d9e8" />
      <circle cx="18" cy="32" r="2" fill="#ff2a6d" />
    </svg>
  );
}
