import hashlib
from flask import Blueprint, render_template, request, redirect, session, url_for 
from globals import db_req
from config import UserConfig
from utils.logger import logger


auth_bp = Blueprint('auth', __name__)


def hash_password(password: str) -> str:
    """
    פונקציית עזר להצפנת סיסמה. מקבלת סיסמה כטקסט גלוי ומחזירה אותה מוצפנת.
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

@auth_bp.route("/login", methods=['GET', 'POST'])
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
                logger.info(f"|auth_routes.py| login of {response.get("username")} was completed")
                # ------------------------------------
                return render_template("login_page.html", success=f"Login Completed Successfully! Welcome {response.get('username')}", redirect_url=url_for('main.home'))
            else:
                logger.error("|auth_routes.py| response from db server wasn't ok during login")
                error_msg = response.get("error") if response else "Internal Communication Error, Try Again"
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
    try:
        session.clear() # מנקה את כל המידע מה-Session (מנתק את המשתמש)
        return redirect(url_for('main.home'))
    except Exception as e:
        logger.exception("|auth_routes.py| Error in logout")

        


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
