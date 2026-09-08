/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          primary: '#0F172A',
          secondary: '#2563EB',
          background: '#F8FAFC',
          card: '#FFFFFF',
          success: '#16A34A',
          warning: '#F59E0B',
          critical: '#DC2626',
          text: '#1E293B',
        },
        investigation: {
          950: '#06090e',
          900: '#0b111b',
          850: '#101926',
          800: '#162234',
          700: '#1f314c',
          600: '#2b446a',
          500: '#3b5f93',
          400: '#5a86c4',
          300: '#8baedd',
          200: '#bcd4f1',
          100: '#e1ecf9',
          50: '#f2f7fc'
        },
        cyber: {
          cyan: '#0284c7',
          indigo: '#2563eb',
          danger: '#dc2626',
          warning: '#f59e0b',
          success: '#16a34a',
          vasp: '#ea580c'
        }
      }
    },
  },
  plugins: [],
}
