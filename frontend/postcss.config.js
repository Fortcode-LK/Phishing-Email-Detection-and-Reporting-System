import { resolve } from 'path';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));

export default {
  plugins: {
    tailwindcss: { config: resolve(__dirname, 'tailwind.config.js') },
    autoprefixer: {},
  },
};
