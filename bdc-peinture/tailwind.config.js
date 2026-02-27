/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/*.py",
    "./apps/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        // Couleurs personnalisées BDC Peinture
        "statut-a-traiter": "#f59e0b",   // amber-500
        "statut-a-faire": "#3b82f6",      // blue-500
        "statut-en-cours": "#8b5cf6",     // violet-500
        "statut-a-facturer": "#f97316",   // orange-500
        "statut-facture": "#22c55e",      // green-500
      },
    },
  },
  plugins: [],
}
