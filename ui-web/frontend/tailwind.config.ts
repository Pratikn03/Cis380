import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        sans: ["IBM Plex Sans", "sans-serif"],
      },
      colors: {
        ink: "var(--ink)",
        fog: "var(--fog)",
        sand: "var(--sand)",
        moss: "var(--moss)",
        ember: "var(--ember)",
        panel: "var(--panel)",
        line: "var(--line)",
      },
      boxShadow: {
        lift: "0 20px 50px rgba(15, 23, 42, 0.15)",
        card: "0 12px 30px rgba(15, 23, 42, 0.12)",
      },
    },
  },
  plugins: [],
} satisfies Config;
