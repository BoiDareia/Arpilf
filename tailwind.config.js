/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./layouts/**/*.html"],
  theme: {
    extend: {
      colors: {
        primary: "#003366",
        accent: "#fecb00",
        secondary: "#f8f9fa",
      },
      fontSize: {
        base: "18px",
      },
    },
  },
  plugins: [],
};
