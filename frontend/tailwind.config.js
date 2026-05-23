/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: "#1A1D2E",
        border: "#2D2D44",
        accent: "#4A90D9",
        "accent-hover": "#357ABD",
      },
    },
  },
  plugins: [],
};
