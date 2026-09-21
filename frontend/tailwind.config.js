/** @type {import('tailwindcss').Config} */

/**
 * Palette follows the conventions of Indian government portals (india.gov.in,
 * data.gov.in, MyGov) and the Guidelines for Indian Government Websites (GIGW):
 * a deep institutional navy for chrome, the tricolour's saffron and green used
 * sparingly as accents and status colours, and generous neutral greys so that
 * dense tabular data stays readable on low-quality office displays.
 *
 * Every foreground/background pair used in the UI clears WCAG-AA (4.5:1) on
 * white, and the status colours are always paired with a dot or a word so that
 * colour alone never carries meaning.
 */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: ['class', '[data-contrast="high"]'],
  theme: {
    extend: {
      colors: {
        // Institutional navy - headers, primary actions, body text.
        ink: {
          50: '#f4f6fa',
          100: '#e6ebf3',
          200: '#ccd5e4',
          300: '#a5b4cd',
          400: '#728ab0',
          500: '#4e6a94',
          600: '#3a5177',
          700: '#2f4262',
          800: '#26344c',
          900: '#16233a',
          950: '#0d1626',
        },
        // Tricolour saffron - warnings, "needs attention", accent rules.
        saffron: {
          50: '#fff8ed',
          100: '#ffeed3',
          200: '#ffd9a5',
          300: '#ffbd6d',
          400: '#ff9832',
          500: '#f97b0b',
          600: '#dd5d06',
          700: '#b74309',
          800: '#94350f',
          900: '#7a2d10',
        },
        // Tricolour green - completion, healthy utilisation, success.
        moss: {
          50: '#f1f9f2',
          100: '#def0e1',
          200: '#bfe1c6',
          300: '#92cb9e',
          400: '#5fae70',
          500: '#3b8f4e',
          600: '#2a723c',
          700: '#235b31',
          800: '#1f4a2a',
          900: '#1a3d24',
        },
        // Ashoka blue - used only for the emblem rule and the chakra accent.
        chakra: '#06038d',
      },
      fontFamily: {
        // Noto Sans carries Devanagari properly; the rest are system fallbacks
        // so the portal still renders correctly with no webfont available.
        sans: [
          'Noto Sans',
          'Inter',
          'Segoe UI',
          'system-ui',
          '-apple-system',
          'sans-serif',
        ],
        devanagari: ['Noto Sans Devanagari', 'Noto Sans', 'Nirmala UI', 'sans-serif'],
      },
      fontSize: {
        // Driven by the accessibility toolbar (A- / A / A+), which sets a
        // root font-size multiplier rather than rewriting every class.
        base: ['1rem', { lineHeight: '1.6' }],
      },
      boxShadow: {
        card: '0 1px 2px rgba(13, 22, 38, 0.06), 0 1px 3px rgba(13, 22, 38, 0.08)',
        raised: '0 4px 14px rgba(13, 22, 38, 0.10)',
        header: '0 2px 4px rgba(13, 22, 38, 0.08)',
      },
      borderRadius: {
        // Government portals read as "official" with restrained corners.
        DEFAULT: '0.25rem',
      },
    },
  },
  plugins: [],
}
