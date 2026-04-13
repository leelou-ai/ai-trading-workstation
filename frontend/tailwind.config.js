/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        'terminal-bg': '#0d1117',
        'terminal-panel': '#1a1a2e',
        'terminal-card': '#161b22',
        'terminal-border': '#30363d',
        'terminal-text': '#e6edf3',
        'terminal-muted': '#7d8590',
        'accent-yellow': '#ecad0a',
        'accent-blue': '#209dd7',
        'accent-purple': '#753991',
        'gain': '#3fb950',
        'loss': '#f85149',
      },
    },
  },
  plugins: [],
}
