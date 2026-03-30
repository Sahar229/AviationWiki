from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from db_client import *
import random
import string
from models import *
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
db_req = DatabaseClient()

app = Flask(__name__)
app.secret_key = 'super_secret_key'
socketio = SocketIO(app)

game_manager = RoomManager()

@app.route("/")
def home() -> str:
    """
    נתיב לעמוד הבית הראשי של האתר.
    מחזיר: מחרוזת של קובץ ה-HTML רונדר.
    """
    return render_template("home_page.html")

@app.route("/learning")
def learning_page() -> str:
    """
    נתיב לעמוד הלמידה (מכיל את חומרי הלימוד בנושא תעופה).
    מחזיר: מחרוזת של קובץ ה-HTML רונדור.
    """
    return render_template("learning_page.html")


@app.route("/login", methods=['GET', 'POST'])
def login_page() -> str:
    """
    נתיב לעמוד ההתחברות.
    מטפל גם בהצגת טופס ההתחברות (GET) וגם בשליחת הנתונים לשרת ה-DB (POST).
    מחזיר: מחרוזת HTML רונדר (עם או בלי הודעות שגיאה/הצלחה).
    """
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        response = db_req.send_request("LOGIN_REQUEST", {
            "email": email, 
            "password": password
        })
        if response and response.get("status") == "ok":
            # --- כאן קורה הקסם: המשתמש מחובר! ---
            session['user_id'] = response.get("user_id")
            session['username'] = response.get("username")
            # ------------------------------------
            return render_template("login_page.html", success=f"Login Completed Successfully! Welcome {response.get('username')}", redirect_url=url_for('home'))
        else:
            error_msg = response.get("error") if response else "Internal Communication Error, Try Again"
            return render_template("login_page.html", error=error_msg)
        
    return render_template("login_page.html")


@app.route("/logout")
def logout(): 
    """
    נתיב לביצוע התנתקות
   .מנקה את נתוני הסשן ומעביר את המשתמש חזרה לעמוד הבית
   מחזירה: אובייקט הפניה של פלסק
    """
    session.clear() # מנקה את כל המידע מה-Session (מנתק את המשתמש)
    return redirect(url_for('home'))

@app.route("/register", methods=['GET', 'POST'])
def register_page() -> str:
    """
    נתיב לעמוד ההרשמה
    מוודא שהסיסמאות תואמות ושולח בקשת יצירת משתמש לשרת הנתונים
    מחזיר: מחרוזת HTML המכילה הודעות רלוונטיות או את טופס ההרשמה.
    """
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
        if password == password2 and len(password) >= 6:
            response = db_req.send_request("REGISTER_REQUEST", {
                "username": username,
                "email": email,
                "password": password
            })
            
            if response and response.get("status") == "ok":
                return render_template("register_page.html", success="Register Complteted Successfully!", redirect_url=url_for('login_page'))
            
            else:
                error_msg = response.get("error") if response else "Internal Server Problem"
                return render_template("register_page.html", error=error_msg)
        elif password != password2:
            error_msg = "Passwords Not Matching"
            return render_template("register_page.html", error=error_msg)
        elif len(password) < 6:
            error_msg = "Password Must Be At Least 6 Characters"
            return render_template("register_page.html", error=error_msg)
        else:
            error_msg = "Internal Server Problem"
            return render_template("register_page.html", error=error_msg)
    return render_template("register_page.html")

@app.route("/quiz_lobby")
def quiz_lobby():
    """
    נתיב ללובי החידונים.
    חסום למשתמשים שאינם מחוברים. מושך ומציג את הסטטיסטיקות של השחקן.
    """

    if 'user_id' not in session or 'username' not in session:
        return render_template("login_page.html", error="You must be logged in to access the Quiz Lobby")

    user_id = session['user_id']
    
    response = db_req.send_request("GET_STATS_REQUEST", {"user_id": user_id})
    
    user_stats = {
        "wins": 0, 
        "games_played": 0, 
        "total_correct_answers": 0
    }
    

    if response and response.get("status") == "ok":
        user_stats = response.get("stats")
        
    return render_template("quiz_lobby.html", stats=user_stats)

@app.route("/room/<room_code>")
def quiz_room(room_code):
    """
    נתיב לחדר ההמתנה של המשחק.
    מוודא שהמשתמש מחובר, ושהוא אכן חלק מרשימת השחקנים בחדר.
    """
    if 'username' not in session:
        return redirect(url_for('login_page'))
    
    username = session['username']
    room = game_manager.get_room(room_code)
    
    # אם החדר לא קיים או שהשחקן לא ברשימה שלו - נזרוק אותו חזרה ללובי
    if not room or username not in room.players:
        return redirect(url_for('quiz_lobby'))
    
    # בודקים האם המשתמש הנוכחי הוא המארח (כדי שנדע אם להציג לו את כפתור "התחל משחק")
    is_host = (room.host == username)
    
    return render_template("quiz_room.html", room_code=room_code, is_host=is_host, max_players=room.max_players)
# ==========================================
# WebSocket Events (Socket.IO)
# ==========================================



# הגדרת לוגים צבעוניים וברורים בטרמינל
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QuizServer")

@socketio.on('create_room')
def handle_create_room(data):
    user = session.get('username')
    logger.info(f"--- [START CREATE_ROOM] --- User: {user}")
    logger.info(f"Payload received: {data}")

    try:
        max_p = int(data.get('max_players', 4))
        is_p = data.get('is_private', False)
        
        new_room = game_manager.create_room(user, is_p, max_p)
        logger.info(f"Room Created in Memory: {new_room.code}")
        
        join_room(new_room.code)
        
        # הלוג הקריטי - האם שלחנו את האישור?
        logger.info(f"Emitting 'room_created' for room {new_room.code}")
        emit('room_created', {'room_code': new_room.code, 'room_data': new_room.to_dict()})

        if not is_p:
            broadcast_public_rooms()
    except Exception as e:
        logger.error(f"Error: {e}")


@socketio.on('join_room_request')
def handle_join_room(data):
    room_code = data.get('room_code', '').upper()
    username = session.get('username')
    
    room = game_manager.get_room(room_code)
    
    if not room:
        emit('join_error', {'message': 'Room not found.'})
        return
        
    # מנסים להוסיף את השחקן למחלקת החדר
    success, message = room.add_player(username)
    
    if not success:
        emit('join_error', {'message': message})
        return
        
    # הכל תקין
    join_room(room_code)
    emit('room_joined', {'room_code': room_code, 'room_data': room.to_dict()})
    emit('player_joined', {'username': username, 'room_data': room.to_dict()}, to=room_code)
    
    broadcast_public_rooms()


@socketio.on('get_public_rooms')
def handle_get_public_rooms():
    broadcast_public_rooms()


def broadcast_public_rooms():
    # פשוט קוראים לפונקציה של ה-Manager ומשדרים את התוצאה
    public_rooms = game_manager.get_public_waiting_rooms()
    socketio.emit('public_rooms_update', public_rooms)

@socketio.on('join_room_socket')
def handle_join_room_socket(data):
    """
    נקרא כשהעמוד של חדר ההמתנה נטען.
    מצרף את חיבור הסוקט החדש של המשתמש לחדר הוירטואלי, ומשדר לכולם את רשימת השחקנים.
    """
    room_code = data.get('room_code')
    room = game_manager.get_room(room_code)
    
    if room:
        # צירוף הסוקט לחדר
        join_room(room_code)
        # שידור רשימת השחקנים המעודכנת לכל מי שבחדר
        emit('update_players', {'players': room.players}, to=room_code)




if __name__ == "__main__":
    socketio.run(app, 
                 debug=True, 
                 port=5000, 
                 certfile='cert.pem', 
                 keyfile='key.pem')