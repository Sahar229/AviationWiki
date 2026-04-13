import random, datetime, time
import uuid

from flask import Blueprint, render_template, request, redirect, session, url_for, jsonify
from globals import db_req, email_sender_tool, active_sessions
from config import UserConfig
from utils.logger import logger
from utils.crypto_utils import hash_password

auth_bp = Blueprint('auth', __name__)

login_attempts = {}


@auth_bp.route("/login", methods=['GET', 'POST'])
def login_page() -> str:
    """
    נתיב לעמוד ההתחברות.
    מטפל גם בהצגת טופס ההתחברות וגם בשליחת הנתונים לשרת בסיס נתונים.
    מחזיר: מחרוזת הטמל רונדר (עם או בלי הודעות שגיאה/הצלחה).
    """
    try:
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']


            user_attempt_data = login_attempts.get(email, {"attempts": 0, "lockout_time": 0})
            if time.time() < user_attempt_data["lockout_time"]:
                remaining_time = int(user_attempt_data["lockout_time"] - time.time())
                # המשתמש נעול

                return render_template("login_page.html", error=f"Account locked. Try again in {remaining_time} seconds."), 403
            

            hashed_pw = hash_password(password)
            response = db_req.send_request("LOGIN_REQUEST", {
                "email": email, 
                "password": hashed_pw
            })
            if response and response.get("status") == "ok":

                username = response.get("username")
                session['user_id'] = response.get("user_id")
                session['username'] = username
                logger.info(f"|auth_routes.py| login of {response.get('username')} was completed")
                login_token = str(uuid.uuid4())
                session['login_token'] = login_token 
                
                # מעדכנים בשרת שהטוקן החוקי היחיד למשתמש הזה הוא הטוקן החדש
                active_sessions[username] = login_token
                return render_template("login_page.html", success=f"Login Completed Successfully! Welcome {response.get('username')}", redirect_url=url_for('main.home'))
            else:
                user_attempt_data["attempts"] += 1
                if user_attempt_data["attempts"] >= UserConfig.MAX_ATTEMPTS:
                    logger.warning(f"|auth_routes.py| {email} was locked out because he tried loggin in too much")
                    user_attempt_data["lockout_time"] = time.time() + UserConfig.LOCKOUT_DURATION
                    
                login_attempts[email] = user_attempt_data

                logger.warning(f"|auth_routes.py| {email} didn't succeseed in loggin in")
                if response and user_attempt_data["attempts"] < UserConfig.MAX_ATTEMPTS:
                    error_msg = response.get("error") + "\n You have " + str(UserConfig.MAX_ATTEMPTS - user_attempt_data["attempts"]) + " attempted remaining"
                elif response:
                    remaining_time = int(user_attempt_data["lockout_time"] - time.time())
                    error_msg = f"Account locked. Try again in {remaining_time} seconds."
                else:
                    error_msg = "Internal Communication Error, Try Again"
                return render_template("login_page.html", error=error_msg)
        return render_template("login_page.html")
    except Exception as e:
        logger.exception("|auth_routes.py| Error in login")


@auth_bp.route("/logout")
def logout(): 
    """
    נתיב לביצוע התנתקות
   .מנקה את נתוני הסשן ומעביר את המשתמש חזרה לעמוד הבית
   מחזירה: אובייקט הפניה של פלסק
    """
    session.clear() # מנקה את כל המידע מהסשן
    return redirect(url_for('main.home'))

        


@auth_bp.route("/register", methods=['GET', 'POST'])
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
                    logger.info(f"|auth_routes.py| register was completed for {username}")
                    return render_template("register_page.html", success="Register Complteted Successfully!", redirect_url=url_for('auth.login_page'))
                
                else:
                    error_msg = response.get("error") if response else "Internal Server Problem"
                    logger.error(f"|auth_routes.py| error while registering in the db for {username}")
                    return render_template("register_page.html", error=error_msg)
                
            elif password != password2:
                error_msg = "Passwords Not Matching"
                logger.warning(f"|auth_routes.py| Registration failed for '{username}': Passwords Not Matching")
                return render_template("register_page.html", error=error_msg)
            
            elif len(password) < UserConfig.MIN_PASSWORD_LENGTH:
                error_msg = f"Password Must Be At Least {UserConfig.MIN_PASSWORD_LENGTH} Characters"
                logger.warning(f"|auth_routes.py| Registration failed for '{username}': Password less than {UserConfig.MIN_PASSWORD_LENGTH} characters")
                return render_template("register_page.html", error=error_msg)
            
            else:
                error_msg = "Internal Server Problem"
                logger.error("|auth_routes.py| error while registering!")
                return render_template("register_page.html", error=error_msg)
        return render_template("register_page.html")
    except Exception as e:
        logger.exception(f"|auth_routes.py| Error in register")

@auth_bp.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password() -> str:
    """
    נתיב לעמוד שכחתי סיסמה
    מבצע את פעולת שליחת סיסמת אימות 
    """
    if request.method == 'GET':
        return render_template('forgot_password.html')
    
    data = request.get_json()
    action = data.get('action')

    
    if action == 'send_code':
        logger.info("hey")
        email = data.get('email')
        response = db_req.send_request("EMAIL_EXISTS",{"email": email})
        if response.get("status") == "ok":
            # הגרלת קוד בן 6 ספרות
            verification_code = str(random.randint(100000, 999999))
            
            # שמירת הקוד והאימייל בסשן כדי שנזכור אותם לשלב הבא
            session['reset_code'] = verification_code
            session['reset_email'] = email

            email_msg = render_template('email_msg.html', code=verification_code)

            email_sender_tool.send_email(email, "AviationWiki Reset Code",email_msg,True)
            logger.info(f"Sending code {verification_code} to {email}") # רק לבדיקות
            session['reset_timestamp'] = datetime.datetime.now(datetime.timezone.utc).timestamp()
            return jsonify({"status": "ok", "message": "Code sent"})
        else:
            logger.error("|auth_routes.py| response from db server failed during reset-email")
            error_msg = response.get("error") if response else "Internal Communication Error, Try Again"
            return jsonify({"status": "fail", "message": error_msg}), 400
        
    elif action == 'verify_code':
        user_code = data.get('code')
        correct_code = session.get('reset_code')
        timestamp = session.get('reset_timestamp')

        if not timestamp:
            return jsonify({"status": "error", "message": "Session invalid"}), 400
        
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        diff_minutes = (now - timestamp) / 60

        if diff_minutes > 10:
            # הקוד פג תוקף - מנקים את הסשן
            session.pop('reset_code', None)
            session.pop('reset_email', None)
            session.pop('reset_timestamp', None)
            return jsonify({"status": "expired", "message": "Expired Code"}), 400
        
        if user_code == correct_code:
            return jsonify({"status": "ok", "message": "Code verified"})
        else:
            return jsonify({"status": "error", "message": "Invalid code"}), 400
        
    
    elif action == 'update_password':
        new_password = data.get('new_password')
        new_password2 = data.get('new_password2')
        email_to_update = session.get('reset_email') # זוכרים לאיזה אימייל לשנות
        
        if not email_to_update:
            return jsonify({"status": "error", "message": "Session expired"}), 400
        if new_password != new_password2:
            return jsonify({"status": "error", "message": "Passwords Not Matching"}), 400
        if len(new_password) < UserConfig.MIN_PASSWORD_LENGTH:
            return jsonify({"status": "error", "message": f"Password Must Be At Least {UserConfig.MIN_PASSWORD_LENGTH} Characters"}), 400

        hashed_pw = hash_password(new_password)
        response = db_req.send_request("UPDATE_PASSWORD",{"email": email_to_update, "new_password":hashed_pw})


        # מחיקת הנתונים הרגישים מהסשן בסיום
        session.pop('reset_code', None)
        session.pop('reset_email', None)
        if response.get("status") == "ok":
            return jsonify({"status": "ok", "message": "Password updated successfully"})
        else:
            logger.error("|auth_routes.py| response from db server failed during update_password")
            error_msg = response.get("error") if response else "Internal Communication Error, Try Again"
            return jsonify({"status": "fail", "message": error_msg}), 400
    
    return jsonify({"status": "error", "message": "Unknown action"}), 400
    
