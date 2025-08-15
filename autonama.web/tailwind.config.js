/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Pure black and white glossy theme
        'glossy-black': '#000000',
        'glossy-dark': '#0a0a0a',
        'glossy-gray': '#1a1a1a',
        'glossy-light-gray': '#2a2a2a',
        'glossy-border': '#333333',
        'glossy-text': '#ffffff',
        'glossy-text-secondary': '#cccccc',
        'glossy-text-muted': '#999999',
        'glossy-accent': '#ffffff',
        'glossy-highlight': '#f0f0f0',
        
        // Light theme - pure white and gray
        'light-pure': '#ffffff',
        'light-gray': '#f8f9fa',
        'light-border': '#e9ecef',
        'light-text': '#000000',
        'light-text-secondary': '#333333',
        'light-text-muted': '#666666',
        'light-accent': '#000000',
        },
      fontFamily: {
        'work-sans': ['"Work Sans"', 'sans-serif'],
        'noto-sans': ['"Noto Sans"', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'glossy-gradient': 'linear-gradient(135deg, #000000 0%, #1a1a1a 100%)',
        'glossy-card': 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)',
        'light-gradient': 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
        'light-card': 'linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'rotate-slow': 'rotate 2s linear infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        rotate: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(255, 255, 255, 0.1)' },
          '100%': { boxShadow: '0 0 20px rgba(255, 255, 255, 0.3)' },
        },
      },
      boxShadow: {
        'glossy': '0 8px 32px rgba(0, 0, 0, 0.4), 0 4px 16px rgba(0, 0, 0, 0.2)',
        'glossy-lg': '0 16px 64px rgba(0, 0, 0, 0.5), 0 8px 32px rgba(0, 0, 0, 0.3)',
        'glossy-card': '0 4px 20px rgba(0, 0, 0, 0.3), 0 2px 8px rgba(0, 0, 0, 0.2)',
        'light': '0 4px 20px rgba(0, 0, 0, 0.1), 0 2px 8px rgba(0, 0, 0, 0.05)',
        'light-lg': '0 16px 64px rgba(0, 0, 0, 0.1), 0 8px 32px rgba(0, 0, 0, 0.05)',
      },
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries'),
  ],
}
