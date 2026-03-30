// static/js/room.js

const socket = io();

// כשהחיבור מצליח, נבקש מהשרת להכניס אותנו שוב לחדר המבוקש
socket.on('connect', () => {
    console.log('Connected to Room WebSocket!');
    socket.emit('join_room_socket', { room_code: ROOM_CODE });
});

// האזנה לעדכון רשימת השחקנים בחדר
socket.on('update_players', (data) => {
    const playersList = document.getElementById('players-list');
    playersList.innerHTML = ''; // מנקים את הרשימה הקיימת

    data.players.forEach(player => {
        const li = document.createElement('li');
        li.textContent = player;
        
        // הוספת סמיילי למארח (הוא תמיד הראשון ברשימה שלנו)
        if (data.players.indexOf(player) === 0) {
            li.textContent += ' 👑 (Host)';
        }
        
        playersList.appendChild(li);
    });
});

// אם המשתמש הוא המארח, נוסיף מאזין לחיצה לכפתור "התחל משחק"
if (IS_HOST) {
    const startBtn = document.getElementById('start-btn');
    if (startBtn) {
        startBtn.addEventListener('click', () => {
            // כאן בהמשך נשלח בקשה לשרת להתחיל את המשחק
            console.log("Requesting to start game...");
            alert("This will start the game soon!");
            // socket.emit('start_game_request', { room_code: ROOM_CODE });
        });
    }
}
