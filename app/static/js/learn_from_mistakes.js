        let messageCounter = 0;
        
        // הפונקציה הזו תרוץ אוטומטית ברגע שהעמוד מסיים להיטען
        window.addEventListener('DOMContentLoaded', () => {
            // משיכת אלמנט תיבת הטקסט (וודא שה-ID תואם למה שיש לך ב-HTML)
            const chatInput = document.getElementById('chat-input'); 

            // בינתיים נשים פה נתונים פיקטיביים לבדיקה התצוגה.
            // בהמשך נחליף את זה בנתונים האמיתיים שיגיעו מה-Flask (מהמשתנה room.errors)
            const mistakesData = serverMistakes || [];

            // בודקים שיש בכלל טעויות לפני שמייצרים את ההודעה
            if (mistakesData.length > 0 && chatInput) {
                // בניית ההקדמה של ההודעה (באנגלית, כי הגדרנו את המודל לדבר אנגלית)
                let autoMessage = "Hi AI Tutor! I just finished my aviation quiz and made a few mistakes. Can you help me understand them?\n\n";
                
                // מעבר על כל הטעויות והוספתן לטקסט בצורה מסודרת
                mistakesData.forEach((mistake, index) => {
                    autoMessage += `Mistake #${index + 1}:\n`;
                    autoMessage += `- Question: "${mistake.question}"\n`;
                    autoMessage += `- I answered: "${mistake.user_answer}"\n`;
                    autoMessage += `- Correct answer: "${mistake.correct_answer}"\n\n`;
                });
                
                autoMessage += "Please explain these concepts simply.";
                
                // השתלת הטקסט המוכן בתוך תיבת הקלט
                chatInput.value = autoMessage;
            }
        });
        
        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            if (!message) return;

            // 1. הוספת הודעת המשתמש למסך
            appendMessage(message, 'user-msg');
            input.value = ''; // ניקוי שורת הטקסט

            // 2. הוספת הודעת "חושב..." זמנית מצד ה-AI
            const loadingId = appendMessage("Thinking...", 'ai-msg');

            try {
                // 3. שליחת ההודעה לנתיב ה-API שניצור בפייתון
                const response = await fetch('/api/ask_ai', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: message })
                });
                
                const data = await response.json();
                
                // 4. החלפת הודעת ה"חושב..." בתשובה האמיתית מהשרת
                document.getElementById(loadingId).innerHTML = marked.parse(data.answer) || "Error getting response.";
            } catch (e) {
                console.error(e);
                document.getElementById(loadingId).innerText = "Communication error with the server.";
            }
        }

        // פונקציית עזר להוספת בועת צ'אט למסך
        function appendMessage(text, className) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${className}`;
            msgDiv.innerText = text;
            msgDiv.id = 'msg-' + messageCounter + '-'+  Date.now(); // יצירת ID ייחודי לטובת עדכון ההודעה מאוחר יותר
            messageCounter++;

            const container = document.getElementById('chat-messages');
            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight; // גלילה אוטומטית למטה
            
            return msgDiv.id;
        }

        // מאפשר שליחה בעזרת מקש האנטר
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
