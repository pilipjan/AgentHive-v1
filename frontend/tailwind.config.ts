import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        hive: {
          50: "#fdf8ee",
          100: "#f9eecd",
          200: "#f4dd96",
          300: "#ecc458",
          400: "#e6ad2d",
          500: "#d99015",
          600: "#bc6f0f",
          700: "#954e10",
          800: "#793e14",
          900: "#653414",
        },
      },
    },
  },
  plugins: [],
};

export default config;
