// static/js/room.js

const socket = io();

// Cache views
const waitingView = document.getElementById('waiting-view');
const playingView = document.getElementById('playing-view');
const feedbackView = document.getElementById('feedback-view');
const finalView = document.getElementById('final-view');

let currentTimer = null;
let currentScoreMap = {};

// Helper to switch views
function showView(viewElement) {
    waitingView.style.display = 'none';
    playingView.style.display = 'none';
    feedbackView.style.display = 'none';
    finalView.style.display = 'none';
    if(viewElement) viewElement.style.display = 'block';
}

socket.on('connect', () => {
    console.log('Connected to Room WebSocket!', MY_USERNAME);
    socket.emit('join_room_socket', { room_code: ROOM_CODE });
});

socket.on('update_players', (data) => {
    const playersList = document.getElementById('players-list');
    if (playersList) {
        playersList.innerHTML = '';
        data.players.forEach(player => {
            const li = document.createElement('li');
            li.textContent = player;
            if (data.players.indexOf(player) === 0) {
                li.textContent += ' 👑 (Host)';
            }
            playersList.appendChild(li);
        });
        
        // Update live scoreboard structure initially
        data.players.forEach(p => {
             if (!(p in currentScoreMap)) {
                 currentScoreMap[p] = 0;
             }
        });
    }
});

// Start button click
if (IS_HOST) {
    const startBtn = document.getElementById('start-btn');
    if (startBtn) {
        startBtn.addEventListener('click', () => {
            socket.emit('start_game_request', { room_code: ROOM_CODE });
        });
    }
}

// =======================
// Game Events
// =======================

socket.on('game_started', () => {
    console.log("Game started by host");
});

socket.on('start_round', (data) => {
    showView(playingView);
    renderScoreboard();
    
    // Set Question
    const totalQ = data.total_questions || 10;
    document.getElementById('q-number').innerText = `Question ${data.question_number}/${totalQ}`;
    document.getElementById('question-text').innerText = data.question.question_text;
    
    // Set Timer
    let duration = data.duration;
    document.getElementById('timer').innerText = duration;
    
    if (currentTimer) clearInterval(currentTimer);
    currentTimer = setInterval(() => {
        duration--;
        if (duration >= 0) {
            document.getElementById('timer').innerText = duration;
        } else {
            clearInterval(currentTimer);
        }
    }, 1000);
    
    // Set Options
    const optionsContainer = document.getElementById('options-container');
    optionsContainer.innerHTML = '';
    
    data.question.options.forEach(opt => {
        const btn = document.createElement('button');
        btn.innerText = opt.text;
        btn.style.padding = '20px';
        btn.style.fontSize = '1.2em';
        btn.style.backgroundColor = '#89c4f4';
        btn.style.color = '#004aad';
        btn.style.border = '2px solid #004aad';
        btn.style.borderRadius = '10px';
        btn.style.cursor = 'pointer';
        btn.style.fontWeight = 'bold';
        
        btn.onclick = () => {
            // Disable all buttons after click
            Array.from(optionsContainer.children).forEach(b => b.disabled = true);
            btn.style.backgroundColor = '#004aad';
            btn.style.color = '#fff';
            
            socket.emit('submit_answer', {
                room_code: ROOM_CODE,
                answer_idx: opt.id
            });
        };
        
        optionsContainer.appendChild(btn);
    });
});

socket.on('scoreboard_update', (data) => {
    currentScoreMap = data.scores;
    renderScoreboard();
});

socket.on('round_results', (data) => {
    if (currentTimer) clearInterval(currentTimer);
    showView(feedbackView);
    currentScoreMap = data.scores;
    renderScoreboard();
    
    const myResult = data.results[MY_USERNAME];
    const prevScore = currentScoreMap[MY_USERNAME] || 0; // Current total
    // To know exactly how many points I just got, we look at the backend delta, or we can just say Correct/Wrong.
    // The requirements say "הראשון שענה נכון מקבל 100 נקודות..." (First correct gets 100).
    
    document.getElementById('feedback-answer').innerText = `The correct answer was: ${data.correct_answer}`;
    
    if (myResult && myResult.correct) {
        document.getElementById('feedback-title').innerText = "Correct! ✅";
        document.getElementById('feedback-title').style.color = "#28a745";
        document.getElementById('feedback-points').innerText = "You earned points based on your speed!";
        document.getElementById('feedback-points').style.color = "#28a745";
    } else if (myResult && myResult.answered) {
        document.getElementById('feedback-title').innerText = "Wrong! ❌";
        document.getElementById('feedback-title').style.color = "#d9534f";
        document.getElementById('feedback-points').innerText = "+0 Points";
        document.getElementById('feedback-points').style.color = "#d9534f";
    } else {
        document.getElementById('feedback-title').innerText = "Time's up! ⏳";
        document.getElementById('feedback-title').style.color = "#f0ad4e";
        document.getElementById('feedback-points').innerText = "+0 Points";
        document.getElementById('feedback-points').style.color = "#f0ad4e";
    }
});

socket.on('game_over', (data) => {
    if (currentTimer) clearInterval(currentTimer);
    showView(finalView);
    
    const winnerDisplay = document.getElementById('winner-display');
    if (data.winners && data.winners.length > 1) {
        winnerDisplay.innerHTML = `Winners: <span id="winner-name" style="color: #28a745; font-size: 1.5em; text-decoration: underline;">${data.winners.join(', ')}</span>`;
    } else if (data.winners && data.winners.length === 1) {
        winnerDisplay.innerHTML = `Winner: <span id="winner-name" style="color: #28a745; font-size: 1.5em; text-decoration: underline;">${data.winners[0]}</span>`;
    } else if (data.standings.length > 0) {
        winnerDisplay.innerHTML = `Winner: <span id="winner-name" style="color: #28a745; font-size: 1.5em; text-decoration: underline;">${data.standings[0].name}</span>`;
    }
    
    const scoreboardList = document.getElementById('final-scoreboard');
    scoreboardList.innerHTML = '';
    
    data.standings.forEach((player, index) => {
        const li = document.createElement('li');
        li.innerText = `${index + 1}. ${player.name} - ${player.score} pts`;
        li.style.padding = '10px';
        li.style.borderBottom = '1px solid #ccc';
        
        if (player.name === MY_USERNAME) {
             li.style.fontWeight = 'bold';
             li.style.color = '#004aad';
             li.style.backgroundColor = '#fff9c4'; // Highlight current user
        }
        
        scoreboardList.appendChild(li);
    });
});

function renderScoreboard() {
    const list = document.getElementById('live-scoreboard');
    const feedbackList = document.getElementById('feedback-scoreboard');
    
    let sorted = Object.entries(currentScoreMap).sort((a,b) => b[1] - a[1]);
    
    [list, feedbackList].forEach(container => {
        if (!container) return;
        container.innerHTML = '';
        sorted.forEach(([name, score], index) => {
            const li = document.createElement('li');
            li.style.padding = '10px';
            li.style.marginBottom = '5px';
            li.style.background = name === MY_USERNAME ? '#e0f7fa' : '#f4f4f4';
            li.style.border = name === MY_USERNAME ? '2px solid #00acc1' : 'none';
            li.style.borderRadius = '5px';
            li.innerText = `${index + 1}. ${name} - ${score} pts`;
            container.appendChild(li);
        });
    });
}