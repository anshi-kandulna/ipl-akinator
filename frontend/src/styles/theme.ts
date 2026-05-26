/**
 * theme.ts — TypeScript mirror of the CSS design tokens.
 *
 * Use these constants when you need token values inside JS/TSX
 * (e.g. Framer Motion inline styles, canvas rendering, etc.).
 * For everything else, prefer the CSS custom properties.
 */

export const colors = {
  // Backgrounds
  bgBase:           '#05070a',
  bgCard:           'rgba(10, 14, 22, 0.92)',
  bgGlass:          'rgba(15, 20, 30, 0.7)',
  bgSurface:        'rgba(255, 255, 255, 0.03)',
  bgSurfaceHover:   'rgba(0, 242, 255, 0.06)',

  // Accents
  accent:           '#00f2ff',
  accentDim:        'rgba(0, 242, 255, 0.12)',
  accentGlow:       'rgba(0, 242, 255, 0.5)',
  accentStrong:     'rgba(0, 242, 255, 0.8)',

  // Gold
  gold:             '#f5c518',
  goldDark:         '#ca8a04',
  goldDim:          'rgba(245, 197, 24, 0.2)',
  goldGlow:         'rgba(245, 197, 24, 0.5)',

  // Text
  textPrimary:      '#ffffff',
  textSecondary:    '#a0aec0',
  textMuted:        '#4a5568',

  // Status
  statusYes:        '#10b981',
  statusYesDim:     'rgba(16, 185, 129, 0.45)',
  statusMaybe:      '#6b7280',
  statusNo:         '#f43f5e',
  statusNoDim:      'rgba(244, 63, 94, 0.45)',

  // Borders
  borderGlass:      'rgba(255, 255, 255, 0.10)',
  borderSubtle:     'rgba(255, 255, 255, 0.05)',
  borderAccent:     'rgba(0, 242, 255, 0.35)',
} as const;

export const fonts = {
  sans: "'Outfit', system-ui, sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace",
} as const;

export const radii = {
  sm:   '4px',
  md:   '8px',
  lg:   '12px',
  xl:   '16px',
  '2xl': '20px',
  '3xl': '24px',
  full: '9999px',
} as const;

export const durations = {
  fast:   150,   // ms
  base:   200,
  slow:   350,
  xslow:  600,
} as const;

export const easings = {
  out:    [0.4, 0, 0.2, 1]    as const,
  spring: [0.34, 1.56, 0.64, 1] as const,
} as const;

/** Pre-built Framer Motion transition presets */
export const transitions = {
  snappy: {
    type: 'tween' as const,
    duration: durations.base / 1000,
    ease: easings.out,
  },
  spring: {
    type: 'spring' as const,
    damping: 20,
    stiffness: 260,
  },
  springBouncy: {
    type: 'spring' as const,
    damping: 14,
    stiffness: 300,
  },
  cardFlip: {
    duration: 0.8,
    type: 'spring' as const,
    stiffness: 80,
    damping: 14,
  },
} as const;

/** Pre-built Framer Motion variant sets */
export const variants = {
  fadeInUp: {
    hidden:  { opacity: 0, y: 24 },
    visible: { opacity: 1, y: 0 },
  },
  fadeIn: {
    hidden:  { opacity: 0 },
    visible: { opacity: 1 },
  },
  scaleIn: {
    hidden:  { opacity: 0, scale: 0.88 },
    visible: { opacity: 1, scale: 1 },
  },
  slideRight: {
    hidden:  { opacity: 0, x: 100, rotateY: 10 },
    visible: { opacity: 1, x: 0, rotateY: 0 },
    exit:    { opacity: 0, x: -100, rotateY: -10 },
  },
  cardReveal: {
    hidden:  { scale: 0.8, opacity: 0, rotateY: 180 },
    visible: { scale: 1,   opacity: 1, rotateY: 0   },
  },
} as const;

export type ColorKey = keyof typeof colors;
