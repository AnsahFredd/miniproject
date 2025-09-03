// tailwind.config.js
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}", // make sure it scans your TSX files
  ],
  theme: {
    extend: {
      colors: {
        secondary: "var(--color-secondary)", // ✅ use CSS variable safely
      },
    },
  },
  plugins: [],
}
