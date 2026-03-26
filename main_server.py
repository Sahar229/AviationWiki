from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from db_client import *

db_req = DatabaseClient()

app = Flask(__name__)
app.secret_key = 'super_secret_key'

@app.route("/")
def home() -> str:
    """
    נתיב לעמוד הבית הראשי של האתר.
    מחזיר: מחרוזת של קובץ ה-HTML المרונדר (Rendered).
    """
    return render_template("home_page.html")

@app.route("/learning")
def learning_page() -> str:
    """
    נתיב לעמוד הלמידה (מכיל את חומרי הלימוד בנושא תעופה).
    מחזיר: מחרוזת של קובץ ה-HTML المרונדר.
    """
    return render_template("learning_page.html")


@app.route("/login", methods=['GET', 'POST'])
def login_page() -> str:
    """
    נתיב לעמוד ההתחברות.
    מטפל גם בהצגת טופס ההתחברות (GET) וגם בשליחת הנתונים לשרת ה-DB (POST).
    מחזיר: מחרוזת HTML المרונדרת (עם או בלי הודעות שגיאה/הצלחה).
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

if __name__ == "__main__":
    app.run(debug=True, ssl_context=("cert.pem", "key.pem"))