export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        midnight: "#07111f",
        cyanGlow: "#58f6ff",
        blueGlow: "#4d7cff",
        panel: "rgba(9, 21, 42, 0.72)"
      },
      boxShadow: {
        neon: "0 0 0 1px rgba(88, 246, 255, 0.18), 0 24px 80px rgba(3, 8, 25, 0.55)"
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(88, 246, 255, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(88, 246, 255, 0.08) 1px, transparent 1px)"
      }
    }
  },
  plugins: []
};
