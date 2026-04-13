        let messageCounter = 0;
        
            // עיצוב הודעת ברירת מחדל מוכנה לשליחה
        window.addEventListener('DOMContentLoaded', () => {
            const chatInput = document.getElementById('chat-input'); 

            const mistakesData = serverMistakes || [];

            if (mistakesData.length > 0 && chatInput) {
                let autoMessage = "Hi AI Tutor! I just finished my aviation quiz and made a few mistakes. Can you help me understand them?\n\n";
                mistakesData.forEach((mistake, index) => {
                    autoMessage += `Mistake #${index + 1}:\n`;
                    autoMessage += `- Question: "${mistake.question}"\n`;
                    autoMessage += `- I answered: "${mistake.user_answer}"\n`;
                    autoMessage += `- Correct answer: "${mistake.correct_answer}"\n\n`;
                });
                
                autoMessage += "Please explain these concepts simply.";
                
                chatInput.value = autoMessage;
            }
        });
        // עיצוב שליחת ההודעה והעברתה לAPI
        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            if (!message) return;

            appendMessage(message, 'user-msg');
            input.value = ''; 


            const loadingId = appendMessage("Thinking...", 'ai-msg');

            try {

                const response = await fetch('/api/ask_ai', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: message })
                });
                
                const data = await response.json();
                

                const rawHtml = marked.parse(data.answer);
                const cleanHtml = DOMPurify.sanitize(rawHtml);
                document.getElementById(loadingId).innerHTML = cleanHtml || "Error getting response.";
            } catch (e) {
                console.error(e);
                document.getElementById(loadingId).innerText = "Communication error with the server.";
            }
        }

        // עיצוב הצגת ההודעה על המסך
        function appendMessage(text, className) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${className}`;
            msgDiv.innerText = text;
            msgDiv.id = 'msg-' + messageCounter + '-'+  Date.now();
            messageCounter++;

            const container = document.getElementById('chat-messages');
            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
            
            return msgDiv.id;
        }


        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
