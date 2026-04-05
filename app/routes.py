import hashlib
from flask import render_template, request, redirect, session, url_for
from globals import app, db_req, game_manager
from config import UserConfig
from utils.logger import logger


def hash_password(password: str) -> str:
    """
    פונקציית עזר להצפנת סיסמה. מקבלת סיסמה כטקסט גלוי ומחזירה אותה מוצפנת.
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

@app.route("/")
def home() -> str:
    """
    נתיב לעמוד הבית הראשי של האתר.
    מחזיר: מחרוזת של קובץ ה-הטמל רונדר.
    """
    return render_template("home_page.html")

@app.route("/learning")
def learning_page() -> str:
    """
    נתיב לעמוד הלמידה (מכיל את חומרי הלימוד בנושא תעופה).
    מחזיר: מחרוזת של קובץ ה-הטמל רונדור.
    """
    return render_template("learning_page.html")


@app.route("/login", methods=['GET', 'POST'])
def login_page() -> str:
    """
    נתיב לעמוד ההתחברות.
    מטפל גם בהצגת טופס ההתחברות וגם בשליחת הנתונים לשרת ה-בסיס נתונים.
    מחזיר: מחרוזת הטמל רונדר (עם או בלי הודעות שגיאה/הצלחה).
    """
    try:
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            hashed_pw = hash_password(password)

            response = db_req.send_request("LOGIN_REQUEST", {
                "email": email, 
                "password": hashed_pw
            })
            if response and response.get("status") == "ok":

                session['user_id'] = response.get("user_id")
                session['username'] = response.get("username")
                logger.info(f"|routes.py| login of {response.get("username")} was completed")
                # ------------------------------------
                return render_template("login_page.html", success=f"Login Completed Successfully! Welcome {response.get('username')}", redirect_url=url_for('home'))
            else:
                logger.error("|routes.py| response from db server wasn't ok during login")
                error_msg = response.get("error") if response else "Internal Communication Error, Try Again"
                return render_template("login_page.html", error=error_msg)
        return render_template("login_page.html")
    except Exception as e:
        logger.exception("|routes.py| Error in login")


@app.route("/logout")
def logout(): 
    """
    נתיב לביצוע התנתקות
   .מנקה את נתוני הסשן ומעביר את המשתמש חזרה לעמוד הבית
   מחזירה: אובייקט הפניה של פלסק
    """
    try:
        session.clear() # מנקה את כל המידע מה-Session (מנתק את המשתמש)
        return redirect(url_for('home'))
    except Exception as e:
        logger.exception("|routes.py| Error in logout")

        


@app.route("/register", methods=['GET', 'POST'])
def register_page() -> str:
    """
    נתיב לעמוד ההרשמה
    מוודא שהסיסמאות תואמות ושולח בקשת יצירת משתמש לשרת הנתונים
    מחזיר: מחרוזת הטמל המכילה הודעות רלוונטיות או את טופס ההרשמה.
    """
    try:
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            password2 = request.form['password2']

            #בדיקת אמינות סיסמה
            if password == password2 and len(password) >= UserConfig.MIN_PASSWORD_LENGTH:
                hashed_pw = hash_password(password)
                response = db_req.send_request("REGISTER_REQUEST", {
                    "username": username,
                    "email": email,
                    "password": hashed_pw
                })
                
                #בדיקת תשובה מהבסיס נתונים
                if response and response.get("status") == "ok":
                    logger.info(f"|routes.py| register was completed for {username}")
                    return render_template("register_page.html", success="Register Complteted Successfully!", redirect_url=url_for('login_page'))
                
                else:
                    error_msg = response.get("error") if response else "Internal Server Problem"
                    logger.error(f"|routes.py| error while registering in the db for {username}")
                    return render_template("register_page.html", error=error_msg)
                
            elif password != password2:
                error_msg = "Passwords Not Matching"
                logger.warning(f"|routes.py| Registration failed for '{username}': Passwords Not Matching")
                return render_template("register_page.html", error=error_msg)
            
            elif len(password) < UserConfig.MIN_PASSWORD_LENGTH:
                error_msg = f"Password Must Be At Least {UserConfig.MIN_PASSWORD_LENGTH} Characters"
                logger.warning(f"|routes.py| Registration failed for '{username}': Password less than {UserConfig.MIN_PASSWORD_LENGTH} characters")
                return render_template("register_page.html", error=error_msg)
            
            else:
                error_msg = "Internal Server Problem"
                logger.error("|routes.py| error while registering!")
                return render_template("register_page.html", error=error_msg)
        return render_template("register_page.html")
    except Exception as e:
        logger.exception(f"|routes.py| Error in register")

@app.route("/quiz_lobby")
def quiz_lobby():
    """
    נתיב ללובי החידונים.
    חסום למשתמשים שאינם מחוברים. מושך ומציג את הסטטיסטיקות של השחקן.
    """
    try:
        if 'user_id' not in session or 'username' not in session:
            logger.warning("|routes.py| tried getting quiz loby while logged out")
            return render_template("login_page.html", error="You must be logged in to access the Quiz Lobby")

        user_id = session['user_id']
        
        response = db_req.send_request("GET_STATS_REQUEST", {"user_id": user_id})
        
        #הגדרת מילון סטאטים
        user_stats = {
            "wins": 0, 
            "games_played": 0, 
            "total_correct_answers": 0
        }
        

        if response and response.get("status") == "ok":
            user_stats = response.get("stats")
        else:
            logger.error("|routes.py| error from db when reaching for stats")
        return render_template("quiz_lobby.html", stats=user_stats)
    except Exception as e:
        logger.exception("|routes.py| Error in quiz loby loading")
        

@app.route("/room/<room_code>")
def quiz_room(room_code):
    """
    נתיב לחדר ההמתנה של המשחק.
    מוודא שהמשתמש מחובר, ושהוא אכן חלק מרשימת השחקנים בחדר.
    """
    try:
        if 'username' not in session:
            return redirect(url_for('login_page'))
        
        username = session['username']
        room = game_manager.get_room(room_code)
        
        # אם החדר לא קיים או שהשחקן לא ברשימה שלו נזרוק אותו חזרה ללובי
        if not room or username not in room.players:
            logger.warning("|routes.py| tried joining a room he's not in")
            return redirect(url_for('quiz_lobby'))
        
        # בודקים האם המשתמש הנוכחי הוא המארח (כדי שנדע אם להציג לו את כפתור "התחל משחק")
        is_host = (room.host == username)
        return render_template("quiz_room.html", room_code=room_code, is_host=is_host, max_players=room.max_players)
    except Exception as e:
        logger.exception("|routes.py| Error in quiz room")

        