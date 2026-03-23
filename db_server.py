import socket
import threading
import sqlite3
import hashlib
import protocol  # האימפורט של הפרוטוקול שיצרנו קודם

# הגדרות השרת   
SERVER_IP = '0.0.0.0'  # מאזין לכל הממשקים
SERVER_PORT = 5002
DB_NAME = "users.db"

def hash_password(password):
    """ לוקח סיסמה רגילה ומחזיר גיבוב (Hash) מאובטח מסוג SHA-256 """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def create_database():
    """ יצירת טבלת המשתמשים אם היא לא קיימת """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("[*] Database ready.")

def handle_client(client_socket, client_address):
    print(f"[+] New connection from {client_address}")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        while True:
            command, params = protocol.receive_message(client_socket)
            if not command:
                break
            
            print(f"Received command: {command} from {client_address}")
            response_data = {}

            # --- לוגיקת התחברות ---
            if command == "LOGIN_REQUEST":
                email = params.get("email")
                password = params.get("password")
                
                hashed_pw = hash_password(password)
                

                cursor.execute("SELECT id, username FROM users WHERE email=? AND password=?", (email, hashed_pw))
                user = cursor.fetchone()
                
                if user:
                    response_data = {"status": "ok", "user_id": user[0], "username": user[1]}
                    print(f"User {email} logged in successfully.")
                else:
                    response_data = {"status": "fail", "error": "Incorrect Email or Password"}
                
                protocol.send_message(client_socket, "LOGIN_RESPONSE", response_data)

            # --- לוגיקת הרשמה ---
            elif command == "REGISTER_REQUEST":
                username = params.get("username")
                email = params.get("email")
                password = params.get("password")
                
                hashed_pw = hash_password(password)
                
                try:
                    # שומרים את hashed_pw במקום את הסיסמה הרגילה
                    cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                                   (username, email, hashed_pw))
                    conn.commit()
                    response_data = {"status": "ok"}
                    print(f"Created new user: {username}")
                except sqlite3.IntegrityError as e:
                    # הופכים את השגיאה לטקסט כדי שנוכל לחפש בתוכה מילים
                    error_message = str(e).lower()
                    
                    if "username" in error_message:
                        response_data = {"status": "fail", "error": "Username Already Exists"}
                    elif "email" in error_message:
                        response_data = {"status": "fail", "error": "Email Already Exists"}
                    else:
                        # מקרה גיבוי למקרה שמשהו אחר השתבש
                        response_data = {"status": "fail", "error": "Username or Email Already Exists"}
                
                protocol.send_message(client_socket, "REGISTER_RESPONSE", response_data)

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        conn.close()
        client_socket.close()
        print(f"[-] Connection closed {client_address}")

def start_server():
    # יצירת בסיס הנתונים בהתחלה
    create_database()
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_IP, SERVER_PORT))
    server.listen(5)
    
    print(f"[*] Database Server listening on port {SERVER_PORT}...")
    
    while True:
        # קבלת חיבור חדש
        client_socket, client_address = server.accept()
        
        # יצירת Thread חדש שיטפל בחיבור הזה
        # זה מאפשר לשרת לחזור מיד למעלה ולהמתין לעוד חיבורים
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

if __name__ == "__main__":
    start_server()
