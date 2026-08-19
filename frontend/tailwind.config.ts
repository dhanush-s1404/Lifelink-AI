import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/lib/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef5ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },
        night: {
          950: "#0b1220",
          900: "#0f172a",
          850: "#131c30",
          800: "#1a2438",
          700: "#24304a",
        },
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(15 23 42 / 0.06), 0 1px 3px 0 rgb(15 23 42 / 0.08)",
        pop: "0 4px 6px -1px rgb(15 23 42 / 0.08), 0 2px 4px -2px rgb(15 23 42 / 0.06)",
        glow: "0 0 0 1px rgb(37 99 235 / 0.25), 0 8px 24px -6px rgb(37 99 235 / 0.35)",
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(135deg, #2563eb 0%, #4f8ff7 55%, #22d3ee 100%)",
        "brand-gradient-soft":
          "linear-gradient(180deg, #eef5ff 0%, #ffffff 60%)",
        "night-gradient":
          "linear-gradient(180deg, #0f172a 0%, #0b1220 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
