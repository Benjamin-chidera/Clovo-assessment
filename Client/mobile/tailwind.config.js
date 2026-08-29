/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        clovo: {
          primary: '#3B49DF',
          primaryDark: '#2B38C6',
          primaryLight: '#EEF2FF',
          streak: '#FF6B00',
          streakSecondary: '#F97316',
          surface: '#F8F9FD',
          card: '#FFFFFF',
          darkCard: '#1C1C1E',
          darkCardTexture: '#2C2C2E',
          textPrimary: '#111827',
          textSecondary: '#6B7280',
          textMuted: '#9CA3AF',
          online: '#10B981',
          onlineLight: '#D1FAE5',
          border: '#E5E7EB',
        },
      },
    },
  },
  plugins: [],
};
