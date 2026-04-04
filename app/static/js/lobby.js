        // --- ניהול ממשק (UI) ---
        let isPrivateRoom = false; 

        function setRoomType(type) {
            const btnPublic = document.getElementById('btn-public');
            const btnPrivate = document.getElementById('btn-private');
            
            if (type === 'private') {
                isPrivateRoom = true;
                btnPrivate.classList.add('active');
                btnPublic.classList.remove('active');
            } else {
                isPrivateRoom = false;
                btnPublic.classList.add('active');
                btnPrivate.classList.remove('active');
            }
        }

        // ==========================================
        // --- תקשורת זמן אמת מול השרת (Socket.IO) ---
        // ==========================================
        
        // 1. פתיחת החיבור מול השרת
        const socket = io();

        // 2. כשהחיבור מצליח, נבקש מיד את רשימת החדרים הפתוחים
        socket.on('connect', () => {
            console.log('Connected to WebSocket server!');
            socket.emit('get_public_rooms');
        });

        socket.on('room_created', (data) => {
            console.log("LOG: SERVER RESPONDED! Room created:", data);
            if(data.room_code) {
                console.log("LOG: Redirecting to:", '/room/' + data.room_code);
                window.location.href = '/room/' + data.room_code;
            } else {
                console.error("LOG ERROR: Received room_created but no room_code!");
            }
        });

        socket.on('room_joined', (data) => {
            console.log('Joined room successfully! Code:', data.room_code);
            // עוברים פיזית לעמוד החדר
            window.location.href = '/room/' + data.room_code;
        });
        
        socket.on('connect_error', (err) => {
            console.error("LOG SOCKET ERROR:", err);
        });

        // 3. קבלת רשימת החדרים מהשרת וציור שלהם במסך
        socket.on('public_rooms_update', (rooms) => {
            const roomsListContainer = document.getElementById('public-rooms-list');
            roomsListContainer.innerHTML = ''; // מנקה את הרשימה הקודמת

            const roomCodes = Object.keys(rooms);
            
            // אם אין חדרים פתוחים
            if (roomCodes.length === 0) {
                roomsListContainer.innerHTML = '<div class="room-item" style="opacity: 0.8; text-align: center; display: block; font-weight: bold;">No public rooms available right now.</div>';
                return;
            }

            // יצירת קוביה לכל חדר פתוח
            roomCodes.forEach(code => {
                const roomData = rooms[code];
                const currentPlayers = roomData.players.length;
                const maxPlayers = roomData.max_players;
                const host = roomData.host;

                const roomDiv = document.createElement('div');
                roomDiv.className = 'room-item';
                roomDiv.innerHTML = `
                    <div>
                        <strong>Room: ${code}</strong><br>
                        <small style="color: #666;">Host: ${host}</small><br>
                        <small style="color: #004aad; font-weight: bold;">Players: ${currentPlayers}/${maxPlayers}</small>
                    </div>
                    <button class="join-btn" onclick="joinSpecificRoom('${code}')">Join</button>
                `;
                roomsListContainer.appendChild(roomDiv);
            });
        });

        // 4. לחיצה על "יצירת חדר חדש"
        document.addEventListener('DOMContentLoaded', () => {
            console.log("LOG: DOM fully loaded and parsed");

            const createBtn = document.getElementById('create-room-btn');
            
            if (!createBtn) {
                console.error("LOG ERROR: Could not find element 'create-room-btn'!");
            } else {
                console.log("LOG: 'create-room-btn' found. Adding listener...");
                
                createBtn.addEventListener('click', (e) => {
                    console.log("LOG: Create button CLICKED!");
                    
                    // בדיקת ערכים לפני שליחה
                    const maxPlayers = document.getElementById('max-players-select')?.value;
                    const numQuestions = document.getElementById('num-questions-select')?.value;
                    console.log("LOG: Max players selected:", maxPlayers);
                    console.log("LOG: Num questions selected:", numQuestions);
                    
                    const payload = {
                        is_private: typeof isPrivateRoom !== 'undefined' ? isPrivateRoom : false,
                        max_players: parseInt(maxPlayers) || 4,
                        num_questions: parseInt(numQuestions) || 10
                    };
                    
                    console.log("LOG: Emitting 'create_room' with payload:", payload);
                    socket.emit('create_room', payload);
                });
            }
        });
        // 5. לחיצה על הצטרפות דרך קוד ידני
        document.getElementById('join-room-btn').addEventListener('click', () => {
            const roomCode = document.getElementById('room-code-input').value.trim().toUpperCase();
            if (roomCode.length !== 4) {
                alert('Please enter a valid 4-character room code.');
                return;
            }
            socket.emit('join_room_request', { room_code: roomCode });
        });

        // פונקציית עזר להצטרפות מתוך כפתור ה-Join ברשימת החדרים הפומביים
        function joinSpecificRoom(code) {
            socket.emit('join_room_request', { room_code: code });
        }

        // 6. טיפול בתשובות מהשרת (הצלחה או שגיאה)

