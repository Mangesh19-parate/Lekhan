import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: ["class", '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "var(--brand-50, #F0F7F4)",
          100: "var(--brand-100)",
          400: "var(--brand-400, #108E5F)",
          500: "var(--brand-500)",
          600: "var(--brand-600)",
          700: "var(--brand-700, #1D4C3E)",
          800: "var(--brand-800)",
          900: "var(--brand-900)",
        },
        approved: {
          100: "var(--approved-100)",
          400: "var(--approved-400, #DFB96E)",
          500: "var(--approved-500)",
          border: "var(--approved-border, #D8B775)",
        },
        canvas: "var(--surface-canvas)",
        sunken: "var(--surface-sunken)",
        card: "var(--surface-card)",
        subtle: "var(--surface-subtle)",
        danger: {
          DEFAULT: "var(--danger-600)",
          500: "var(--danger-500)",
          600: "var(--danger-600)",
          tint: "var(--danger-tint)",
          border: "var(--danger-border)",
        },
        warning: {
          DEFAULT: "var(--warning-500)",
          500: "var(--warning-500)",
          600: "var(--warning-600)",
          tint: "var(--warning-tint)",
          border: "var(--warning-border)",
        },
        success: {
          DEFAULT: "var(--success-500)",
          500: "var(--success-500)",
          600: "var(--success-600)",
          tint: "var(--success-tint)",
          border: "var(--success-border)",
        },
        text: {
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          tertiary: "var(--text-tertiary)",
          muted: "var(--text-muted)",
          "on-dark": "var(--text-on-dark)",
          "on-dark-2": "var(--text-on-dark-2)",
        },
        line: {
          subtle: "var(--line-subtle)",
          medium: "var(--line-medium)",
          strong: "var(--line-strong)",
        },
      },
      borderRadius: {
        input: "var(--radius-input, 8px)",
        card: "var(--radius-card, 12px)",
        pill: "var(--radius-pill, 50px)",
      },
      boxShadow: {
        card: "var(--shadow-card)",
        nav: "var(--shadow-nav)",
        dialog: "var(--shadow-dialog)",
        elevated: "var(--shadow-elevated)",
      },
      fontFamily: {
        ui: ["Inter", "Noto Sans Devanagari", "Helvetica Neue", "Arial", "sans-serif"],
        mono: ["JetBrains Mono", "Courier New", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
