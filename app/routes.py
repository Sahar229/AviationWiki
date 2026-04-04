from flask import render_template, request, redirect, session, url_for
from globals import app, db_req, game_manager
from config import UserConfig



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
        if password == password2 and len(password) >= UserConfig.MIN_PASSWORD_LENGTH:
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
        elif len(password) < UserConfig.MIN_PASSWORD_LENGTH:
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