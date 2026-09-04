/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],

  theme: {
    extend: {
      boxShadow: {
        soft: "0 4px 20px rgba(15, 23, 42, 0.06)",
      },
    },
  },

  plugins: [],
};