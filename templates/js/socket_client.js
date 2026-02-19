/**
 * Socket client — handles game and chat real-time events.
 */
const socket = io();

// --- Connection ---
socket.on('connect', () => {
    console.log('[Socket] Connected');
});

socket.on('disconnect', () => {
    console.log('[Socket] Disconnected');
});

socket.on('error', (data) => {
    showToast(data.message || 'An error occurred', 'error');
});

socket.on('online_count', (data) => {
    const el = document.getElementById('online-count');
    if (el) el.textContent = data.count;
});

// --- Game Events ---
socket.on('game_created', (data) => {
    console.log('[Game] Created:', data);
    window.currentRoom = data.room_code;
    window.location.href = `/game/${data.game_slug}/${data.room_code}`;
});

socket.on('game_joined', (data) => {
    console.log('[Game] Joined:', data);
    window.currentRoom = data.room_code;
    window.gameState = data.state;
    window.yourPlayer = data.your_player;
    if (typeof onGameJoined === 'function') onGameJoined(data);
});

socket.on('game_update', (data) => {
    console.log('[Game] Update:', data);
    window.gameState = data.state;
    if (typeof onGameUpdate === 'function') onGameUpdate(data);
    if (data.game_over) {
        if (typeof onGameOver === 'function') onGameOver(data);
    }
});

socket.on('move_error', (data) => {
    showToast(data.message, 'error');
});

// --- Chat Events ---
socket.on('chat_history', (data) => {
    if (typeof onChatHistory === 'function') onChatHistory(data);
});

socket.on('chat_message', (data) => {
    if (typeof onChatMessage === 'function') onChatMessage(data);
});

// --- Helpers ---
function createGame(gameSlug, isPrivate, password) {
    const data = { game_slug: gameSlug };
    if (isPrivate) { data.is_private = true; data.password = password || ''; }
    socket.emit('create_game', data);
}

function joinGame(roomCode) {
    socket.emit('join_game', { room_code: roomCode });
}

function joinGameWithPassword(roomCode, password) {
    socket.emit('join_game', { room_code: roomCode, password: password });
}

function findMatch(gameSlug) {
    socket.emit('find_match', { game_slug: gameSlug });
}

function makeMove(roomCode, move) {
    socket.emit('make_move', { room_code: roomCode, move: move });
}

function resignGame(roomCode) {
    socket.emit('resign', { room_code: roomCode });
}

function joinChat(roomId) {
    socket.emit('chat_join', { room_id: roomId });
}

function sendChat(roomId, content) {
    socket.emit('chat_send', { room_id: roomId, content: content });
}

// --- Toast notification ---
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `flash-msg ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
}
