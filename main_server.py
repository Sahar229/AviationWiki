from flask import Flask, render_template, request, redirect, url_for, flash
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
        
        
        send_to_db_server("LOGIN_REQUEST",{
            "email": email, 
            "password": password
        })

        
        print(f"Login attempt: {email}, {password}")
        

        return redirect(url_for('home'))
        
    return render_template("login_page.html")

@app.route("/register", methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # TODO: כאן נוסיף את הקוד שמתחבר לשרת ה-Database
        # 1. יצירת Socket
        # 2. שליחת הודעה: "REGISTER|{username}|{email}|{password}"
        # 3. בדיקה אם המשתמש כבר קיים ושמירה
        
        print(f"Register attempt: {username}, {email}, {password}")
        return redirect(url_for('login'))
        
    return render_template("register_page.html")

if __name__ == "__main__":
    app.run(debug=True, ssl_context=("cert.pem", "key.pem"))