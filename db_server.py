import socket
import threading
import sqlite3
import protocol  # האימפורט של הפרוטוקול שיצרנו קודם

# הגדרות השרת
SERVER_IP = '0.0.0.0'  # מאזין לכל הממשקים
SERVER_PORT = 5002
DB_NAME = "users.db"

def create_database():
    #TODO בניית מאגר נתונים 
    pass

def handle_client(client_socket, client_address):
    """
    הפונקציה שרצה בתוך Thread נפרד לכל חיבור שנכנס.
    """
    print(f"[+] New connection from {client_address}")
    
    conn = sqlite3.connect(DB_NAME) # חיבור ל-DB בתוך ה-Thread
    cursor = conn.cursor()

    try:
        while True:
            # 1. קבלת הודעה באמצעות הפרוטוקול שלנו
            command, params = protocol.receive_message(client_socket)
            
            if not command:
                break # אם הצד השני התנתק
            
            print(f"Received command: {command} from {client_address}")
            response_data = {}

            # --- לוגיקת התחברות ---
            if command == "LOGIN_REQUEST":
                email = params.get("email")
                password = params.get("password")
                print(email,password)
                
                # # שאילתה מאובטחת נגד SQL Injection
                # cursor.execute("SELECT id, username, score FROM users WHERE email=? AND password=?", (email, password))
                # user = cursor.fetchone()
                
                # if user:
                #     response_data = {"status": "ok", "user_id": user[0], "username": user[1], "score": user[2]}
                # else:
                #     response_data = {"status": "fail", "error": "Invalid email or password"}
                
                # שליחת התשובה חזרה ל-Flask
                protocol.send_message(client_socket, "LOGIN_RESPONSE", {"status": "ok"})

    #         # --- לוגיקת הרשמה ---
    #         elif command == "REGISTER_REQUEST":
    #             username = params.get("username")
    #             email = params.get("email")
    #             password = params.get("password")
                
    #             try:
    #                 cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
    #                                (username, email, password))
    #                 conn.commit()
    #                 response_data = {"status": "ok"}
    #                 print(f"Created new user: {username}")
    #             except sqlite3.IntegrityError:
    #                 # המייל כבר קיים במערכת
    #                 response_data = {"status": "fail", "error": "Email already exists"}
                
    #             protocol.send_message(client_socket, "REGISTER_RESPONSE", response_data)

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
