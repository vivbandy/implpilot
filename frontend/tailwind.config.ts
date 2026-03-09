import type { Config } from 'tailwindcss'

// Tailwind theme extension maps our CSS token variables to utility classes.
// Components use bg-surface, text-primary, etc. — never hardcoded hex colors.
// See frontend/src/styles/tokens.css for the CSS variable definitions (Section 10.2).
const config: Config = {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Surfaces
        'bg-app':        'var(--color-bg-app)',
        'bg-surface':    'var(--color-bg-surface)',
        'bg-subtle':     'var(--color-bg-subtle)',
        'bg-overlay':    'var(--color-bg-overlay)',

        // Borders
        'border-default': 'var(--color-border)',
        'border-strong':  'var(--color-border-strong)',

        // Text
        'text-primary':   'var(--color-text-primary)',
        'text-secondary': 'var(--color-text-secondary)',
        'text-disabled':  'var(--color-text-disabled)',
        'text-inverse':   'var(--color-text-inverse)',

        // Brand / Interactive
        'brand':         'var(--color-brand)',
        'brand-hover':   'var(--color-brand-hover)',
        'brand-light':   'var(--color-brand-light)',

        // Status colors (muted, not neon)
        'status-green':     'var(--color-status-green)',
        'status-green-bg':  'var(--color-status-green-bg)',
        'status-yellow':    'var(--color-status-yellow)',
        'status-yellow-bg': 'var(--color-status-yellow-bg)',
        'status-red':       'var(--color-status-red)',
        'status-red-bg':    'var(--color-status-red-bg)',
        'status-purple':    'var(--color-status-purple)',
        'status-purple-bg': 'var(--color-status-purple-bg)',
        'status-gray':      'var(--color-status-gray)',
        'status-gray-bg':   'var(--color-status-gray-bg)',

        // Priority colors
        'priority-critical': 'var(--color-priority-critical)',
        'priority-high':     'var(--color-priority-high)',
        'priority-medium':   'var(--color-priority-medium)',
        'priority-low':      'var(--color-priority-low)',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      borderRadius: {
        sm:   'var(--radius-sm)',
        md:   'var(--radius-md)',
        lg:   'var(--radius-lg)',
        pill: 'var(--radius-pill)',
      },
      boxShadow: {
        card:    'var(--shadow-card)',
        popover: 'var(--shadow-popover)',
        modal:   'var(--shadow-modal)',
      },
      fontSize: {
        xs:  ['11px', '1.3'],
        sm:  ['12px', '1.5'],
        md:  ['14px', '1.5'],
        lg:  ['16px', '1.5'],
        xl:  ['18px', '1.3'],
        '2xl': ['22px', '1.3'],
        '3xl': ['28px', '1.2'],
      },
    },
  },
  plugins: [],
}

export default config
