/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
  	extend: {
  		colors: {
  			'base-bg': '#F2F5FB',
  			'surface-1': '#FFFFFF',
  			'surface-2': '#F8FAFE',
  			'surface-3': '#EEF3FB',
  			border: '#D9E2F0',
  			primary: {
  				DEFAULT: '#0F766E',
  				foreground: '#F7FFFD'
  			},
  			'accent-1': '#155EEF',
  			'subtle-1': '#DDF3EE',
  			'subtle-2': '#E7EDFF',
  			'text-high': '#0F172A',
  			'text-dim': '#475569',
  			'text-muted': '#64748B',
  			error: '#DC2626',
  			warning: '#D97706',
  			success: '#059669',
  			background: '#F2F5FB',
  			foreground: '#0F172A',
  			accent: {
  				DEFAULT: '#E7EDFF',
  				foreground: '#0F1F40'
  			},
  			card: {
  				DEFAULT: '#FFFFFF',
  				foreground: '#0F172A'
  			},
  			popover: {
  				DEFAULT: '#FFFFFF',
  				foreground: '#0F172A'
  			},
  			muted: {
  				DEFAULT: '#EEF3FB',
  				foreground: '#475569'
  			},
  			secondary: {
  				DEFAULT: '#EAF0F9',
  				foreground: '#0F172A'
  			},
  			destructive: {
  				DEFAULT: '#DC2626',
  				foreground: '#FFFFFF'
  			},
  			ring: '#0F766E',
  			input: '#C7D4E7'
  		},
  		borderRadius: {
  			lg: '0.5rem',
  			md: 'calc(0.5rem - 2px)',
  			sm: 'calc(0.5rem - 4px)'
  		},
  		keyframes: {
  			'accordion-down': {
  				from: {
  					height: '0'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			},
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)'
  				},
  				to: {
  					height: '0'
  				}
  			}
  		},
  		animation: {
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
};
