/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: "#0A0A0A",
        card: "rgba(10, 10, 10, 0.5)",
        border: "#242424",
        text: "#F0F0F0",
        green: "#00C853",
      },
      fontFamily: {
        champion: ["ChampionGothic", "sans-serif"],
        inter: ["Inter", "sans-serif"],
        hm_text : ["HitmarkerText" , "sans-serif"],
      },
    },
  },
  plugins: [],
}
