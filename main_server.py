from flask import Flask, render_template, request, redirect, url_for, flash, session
import socket
import protocol

DB_IP = '127.0.0.1'
DB_PORT = 5002

def send_to_db_server(command, params):
    """ פונקציית עזר שפותחת חיבור, שולחת ומקבלת תשובה """
    try:
        # פתיחת סוקט לשרת הנתונים
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((DB_IP, DB_PORT))
        
        # שימוש בפרוטוקול שלנו
        protocol.send_message(sock, command, params)
        cmd, response_data = protocol.receive_message(sock)
        
        sock.close()
        return response_data
    except Exception as e:
        print(f"Connection error: {e}")
        return None



app = Flask(__name__)
app.secret_key = 'super_secret_key'

@app.route("/")
def home():
    return render_template("home_page.html")

@app.route("/learning")
def learning_page():
    return render_template("learning_page.html")


@app.route("/login", methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        response = send_to_db_server("LOGIN_REQUEST", {
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
            error_msg = response.get("error") if response else "Intenral Communication Error, Try Again"
            return render_template("login_page.html", error=error_msg)
        
    return render_template("login_page.html")

# נתיב חדש: התנתקות
@app.route("/logout")
def logout():
    session.clear() # מנקה את כל המידע מה-Session (מנתק את המשתמש)
    return redirect(url_for('home'))

@app.route("/register", methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
        if password == password2:
            response = send_to_db_server("REGISTER_REQUEST", {
                "username": username,
                "email": email,
                "password": password
            })
            
            if response and response.get("status") == "ok":
                return render_template("register_page.html", success="Register Complteted Successfully!", redirect_url=url_for('login_page'))
            
            else:
                error_msg = response.get("error") if response else "Internal Server Problem"
                return render_template("register_page.html", error=error_msg)
        else:
            error_msg = "Passwords Not Matching"
            return render_template("register_page.html", error=error_msg)

        
    return render_template("register_page.html")

if __name__ == "__main__":
    app.run(debug=True, ssl_context=("cert.pem", "key.pem"))