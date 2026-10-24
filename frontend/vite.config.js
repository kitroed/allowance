import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
    plugins: [
        sveltekit({
            adapter: adapter({
                fallback: '200.html'
            })
        })
    ],
    server: {
        proxy: {
            '/api': 'http://localhost:5000'
        }
    }
});
