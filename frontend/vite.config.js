import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:5050',
      '/socket.io': {
        target: 'http://127.0.0.1:5050',
        ws: true,
      },
      '/get_player_info.php': 'http://127.0.0.1:5050',
      '/get_neighbor_info.php': 'http://127.0.0.1:5050',
      '/command.php': 'http://127.0.0.1:5050',
      '/get_game_config.php': 'http://127.0.0.1:5050',
      '/get_quest_map.php': 'http://127.0.0.1:5050',
      '/crossdomain.xml': 'http://127.0.0.1:5050',
      '/assets': 'http://127.0.0.1:5050',
      '/stub': 'http://127.0.0.1:5050',
      '/default01.static.socialpointgames.com': 'http://127.0.0.1:5050',
      '/dynamic.flash1.dev.socialpoint.es': 'http://127.0.0.1:5050',
    },
  },
})
