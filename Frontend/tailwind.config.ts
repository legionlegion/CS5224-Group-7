import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#f5f0e8",
        ink: "#102217",
        moss: "#3f7d58",
        leaf: "#68b684",
        sand: "#e7c89b",
        clay: "#bd6f44"
      },
      boxShadow: {
        card: "0 20px 45px rgba(16, 34, 23, 0.12)"
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "sans-serif"]
      }
    }
  },
  plugins: []
};

export default config;
