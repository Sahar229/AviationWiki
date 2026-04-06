from flask import Blueprint, render_template, session, redirect, url_for
from globals import db_req, game_manager
from utils.logger import logger


main_bp = Blueprint('main', __name__)


@main_bp.route("/")
def home() -> str:
    """
    נתיב לעמוד הבית הראשי של האתר.
    מחזיר: מחרוזת של קובץ ה-הטמל רונדר.
    """
    return render_template("home_page.html")

@main_bp.route("/learning")
def learning_page() -> str:
    """
    נתיב לעמוד הלמידה (מכיל את חומרי הלימוד בנושא תעופה).
    מחזיר: מחרוזת של קובץ ה-הטמל רונדור.
    """
    return render_template("learning_page.html")


@main_bp.route("/quiz_lobby")
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
        

@main_bp.route("/room/<room_code>")
def quiz_room(room_code):
    """
    נתיב לחדר ההמתנה של המשחק.
    מוודא שהמשתמש מחובר, ושהוא אכן חלק מרשימת השחקנים בחדר.
    """
    try:
        if 'username' not in session:
            return redirect(url_for('auth.login_page'))
        
        username = session['username']
        room = game_manager.get_room(room_code)
        
        # אם החדר לא קיים או שהשחקן לא ברשימה שלו נזרוק אותו חזרה ללובי
        if not room or username not in room.players:
            logger.warning("|routes.py| tried joining a room he's not in")
            return redirect(url_for('main.quiz_lobby'))
        
        # בודקים האם המשתמש הנוכחי הוא המארח (כדי שנדע אם להציג לו את כפתור "התחל משחק")
        is_host = (room.host == username)
        return render_template("quiz_room.html", room_code=room_code, is_host=is_host, max_players=room.max_players)
    except Exception as e:
        logger.exception("|routes.py| Error in quiz room")