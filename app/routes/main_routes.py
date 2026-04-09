import json

from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from globals import db_req, game_manager
from utils.logger import logger
from google import genai
from google.genai import types
from config import APIConfig
main_bp = Blueprint('main', __name__)

ai_tutor_model = genai.Client(api_key=APIConfig.API_KEY)

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
            logger.warning("|main_routes.py| tried getting quiz loby while logged out")
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
            logger.error("|main_routes.py| error from db when reaching for stats")
        return render_template("quiz_lobby.html", stats=user_stats)
    except Exception as e:
        logger.exception("|main_routes.py| Error in quiz loby loading")
        

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
        session['ai_requests_count'] = 0
        room = game_manager.get_room(room_code)
        
        # אם החדר לא קיים או שהשחקן לא ברשימה שלו נזרוק אותו חזרה ללובי
        if not room or username not in room.players:
            logger.warning("|main_routes.py| tried joining a room he's not in")
            return redirect(url_for('main.quiz_lobby'))
        
        # בודקים האם המשתמש הנוכחי הוא המארח (כדי שנדע אם להציג לו את כפתור "התחל משחק")
        is_host = (room.host == username)
        return render_template("quiz_room.html", room_code=room_code, is_host=is_host, max_players=room.max_players)
    except Exception as e:
        logger.exception("|main_routes.py| Error in quiz room")


@main_bp.route("/learn_from_mistakes", methods=['GET', 'POST'])
def learn_from_mistakes() -> str:
    """
    נתיב לעמוד למידה מטעויות בעזרת בינה מלאכותית.
    מחזיר: מחרוזת של קובץ ה-הטמל רונדר.
    """
    if request.method == 'POST':
        mistakes_json = request.form.get('mistakes')
        if mistakes_json:
            try:
                # המרת המחרוזת חזרה לרשימה של מילונים (Python List)
                mistakes = json.loads(mistakes_json)
                
                # נעביר את הרשימה לעמוד ה-HTML
                return render_template("learn_from_mistakes.html", mistakes=mistakes)
            except json.JSONDecodeError:
                logger.error("|main_routes.py| Failed to parse mistakes JSON")
                
    # אם אין טעויות, או שזו בקשת GET (מישהו הקליד את הכתובת ישירות) - נחזיר ללובי
    logger.warning("|main_routes.py| User tried accessing learn_from_mistakes without data")
    return render_template("home_page.html")


@main_bp.route("/api/ask_ai", methods=['POST'])
def ask_ai():
    """
    פונקציית שימוש בAPI בלימוד עצמי
    """
    ai_requests_count = session.get('ai_requests_count', 0)

    if ai_requests_count >= 3:
        return jsonify({"answer": "You have reached your limit of 3 AI requests for this session. Keep flying!"}), 403
    

    data = request.get_json()
    user_prompt = data.get('prompt', '')
    if not user_prompt:
        return jsonify({"answer": "No prompt provided."}), 400
        
    try:
        # 3. שליחת השאלה של המשתמש למודל
        response = ai_tutor_model.models.generate_content(
            model="gemini-2.5-flash", # השם הזה עובד חלק בספרייה החדשה
            contents=user_prompt,
            # 3. כאן אנחנו מכניסים את האישיות של המורה דרך אובייקט הקינפוג
            config=types.GenerateContentConfig(
                system_instruction="You are a friendly, encouraging, and expert aviation tutor. You explain concepts simply, focus on aviation physics, aircraft systems, and flying rules. Keep your answers concise and clear."
            )
        )
        session['ai_requests_count'] = ai_requests_count + 1
        # 4. חילוץ הטקסט נטו מתוך התשובה
        ai_answer = response.text
        
        return jsonify({"answer": ai_answer})
        
    except Exception as e:
        # במקרה של שגיאה (למשל בעיית אינטרנט או מפתח לא נכון)
        logger.exception(f"Error getting response from api")
        return jsonify({"answer": "My AI brain had a slight malfunction. Please try again."}), 500