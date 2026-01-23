/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Legacy colors (for existing pages)
        'deep-black': '#0a0a0f',
        'charcoal': '#16161d',
        'dark-gray': '#1e1e2e',
        'glow-purple': '#9333ea',
        'glow-blue': '#3b82f6',
        'glow-cyan': '#06b6d4',
        'neon-purple': '#a855f7',
        'neon-blue': '#60a5fa',
        'neon-cyan': '#22d3ee',

        // STEP 8: Warm minimalist system
        // Base tones
        'warm-bg': '#FAFAF9',           // Warm off-white / parchment
        'warm-surface': '#FEFEFE',       // Subtle warm white for cards
        'warm-surface-alt': '#F8F7F6',   // Alternate surface (2-3% variation)

        // Accents (muted, used sparingly)
        'terracotta': {
          50: '#FBF5F3',
          100: '#F7EBE7',
          200: '#EDD6CE',
          300: '#E0BBB0',
          400: '#CE9685',
          500: '#BC7A67',  // Primary - muted terracotta/clay
          600: '#A66555',
          700: '#8A5447',
          800: '#72463D',
          900: '#5E3C35',
        },
        'sage': {
          50: '#F6F7F6',
          100: '#E8EBE8',
          200: '#D4D9D4',
          300: '#B5BDB5',
          400: '#8FA08F',  // Sage green for positive signals
          500: '#748574',
          600: '#5D6C5D',
          700: '#4D584D',
          800: '#424A42',
          900: '#393F39',
        },
        'cocoa': {
          50: '#F7F6F5',
          100: '#EDEAE8',
          200: '#DAD5D0',
          300: '#C2B9B1',
          400: '#A4968C',  // Cocoa gray for neutral
          500: '#8B7D73',
          600: '#76685E',
          700: '#61544D',
          800: '#524741',
          900: '#473E39',
        },

        // Text
        'warm-text': {
          DEFAULT: '#3A3634', // Dark warm gray (never pure black)
          light: '#5C5753',
          lighter: '#7D7975',
          subtle: '#A8A39F',
        },

        // Dividers and borders
        'warm-border': 'rgba(58, 54, 52, 0.12)',
        'warm-divider': 'rgba(58, 54, 52, 0.08)', // Hairline, low-opacity warm gray
      },
      // Font family
      fontFamily: {
        'inter': ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },

      animation: {
        // Legacy animations (for existing pages)
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'slide-up': 'slide-up 0.5s ease-out',
        'fade-in': 'fade-in 0.6s ease-out',
        'float': 'float 6s ease-in-out infinite',
        'gradient': 'gradient 8s ease infinite',

        // STEP 8: Calm animations (slower, ease-out only)
        'calm-fade-in': 'calm-fade-in 0.8s ease-out',
        'calm-slide-up': 'calm-slide-up 0.6s ease-out',
      },
      keyframes: {
        // Legacy keyframes
        'pulse-glow': {
          '0%, 100%': { opacity: '0.5', transform: 'scale(1)' },
          '50%': { opacity: '1', transform: 'scale(1.05)' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        'gradient': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },

        // STEP 8: Calm keyframes (slower, subtle)
        'calm-fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'calm-slide-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      backgroundImage: {
        'radial-glow': 'radial-gradient(circle, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}