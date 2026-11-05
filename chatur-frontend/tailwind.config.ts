import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        sage: '#ccd5ae',
        pistachio: '#e9edc9',
        ivory: '#fefae0',
        sand: '#faedcd',
        clay: '#d4a373',
        mainText: '#000000',
        secondaryText: '#333333',
        chaturBorder: '#ccd5ae',
        inputBg: '#ffffff',
        neutralBg: '#fefae0',
        brand: {
          sage: '#ccd5ae',
          pistachio: '#e9edc9',
          ivory: '#fefae0',
          sand: '#faedcd',
          clay: '#d4a373',
          surface: '#ffffff',
          canvas: '#fefae0',
          ink: '#000000',
          secondary: '#333333',
          line: '#ccd5ae',
        },
        primary: {
          50: '#fefae0',
          100: '#faedcd',
          200: '#e9edc9',
          300: '#ccd5ae',
          400: '#d4a373',
          500: '#d4a373',
          600: '#c49262',
          700: '#b48151',
          800: '#936336',
          900: '#72461f',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        telugu: ['"Noto Sans Telugu"', 'system-ui', 'sans-serif'],
        devanagari: ['"Noto Sans Devanagari"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
