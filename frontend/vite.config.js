import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/BlueAgent/', 
  plugins: [react()],
})
