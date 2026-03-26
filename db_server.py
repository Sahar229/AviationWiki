import socket
import threading
from protocol import *
from db_manager import *

class DatabaseServer:
    """
    מחלקה המייצגת את שרת בסיס הנתונים .
    מקשיבה לבקשות מלקוחות , מנתבת את הבקשות לבסיס נתונים עצמו, ומחזירה תשובה.
    """
    def __init__(self, ip='0.0.0.0', port=5002):
        self.ip = ip
        self.port = port
        self.db = DatabaseManager()

    def process_login(self, client_socket: socket.socket, params) -> None:
        """
        פונקציה המעבדת בקשת התחברות.
        שולפת את הנתונים, מבצעת שאילתה מול בסיס הנתונים, ושולחת תשובה חזרה ללקוח.
        מחזירה: כלום. הפעולה שולחת את הנתונים ישירות לסוקט.
        """
        response_data = {}
        try:
            email = params.get("email")
            password = params.get("password")
            
            user = self.db.login(email,password)
            
            if user:
                response_data = {"status": "ok", "user_id": user[0], "username": user[1]}
                print(f"User {email} logged in successfully.")
            else:
                response_data = {"status": "fail", "error": "Incorrect Email or Password"}
        finally:
            ProtocolTools.send_message(client_socket, "LOGIN_RESPONSE", response_data)
    
    def process_register(self, client_socket: socket.socket, params) -> None:
        """
        פונקציה המעבדת בקשת הרשמה.
        מפעילה את מתודת הרישום בבסיס הנתונים ומחזירה את התוצאה ללקוח.
        מחזירה: כלום. הפעולה שולחת את הנתונים ישירות לסוקט.
        """
        response_data = {}
        try:
            username = params.get("username")
            email = params.get("email")
            password = params.get("password")
            
            response_data = self.db.register(username, email, password)
        finally:
          ProtocolTools.send_message(client_socket, "REGISTER_RESPONSE", response_data)
    


    def handle_client(self, client_socket: socket.socket, client_address) -> None:
        """
        פונקציה הרצה בתהליכון נפרד עבור כל לקוח שמתחבר.
        מאזינה לבקשות נכנסות, מנתבת אותן לפונקציה המתאימה, ובסיום דואגת לסגור את החיבור.
        מחזירה: כלום.
        """
        print(f"[+] New connection from {client_address}")
        try:
            while True:
                command, params = ProtocolTools.receive_message(client_socket)
                if not command:
                    break
        
                print(f"Received command: {command} from {client_address}")

                if command == "LOGIN_REQUEST":
                    self.process_login(client_socket, params)
        
                elif command == "REGISTER_REQUEST":
                    self.process_register(client_socket, params)    

        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()
            print(f"[-] Connection closed {client_address}")

    def start_server(self) -> None:
        """
        פונקציית ההפעלה של השרת.
        פותחת סוקט האזנה ומקבלת חיבורים חדשים בלולאה אינסופית. כל חיבור חדש נפתח ב-Thread משלו.
        מחזירה: כלום.
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.ip, self.port))
        server.listen(5)
        
        print(f"[*] Database Server listening on port {self.port}...")
        
        while True:
            client_socket, client_address = server.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_thread.start()



if __name__ == "__main__":
    db_ser = DatabaseServer()
    db_ser.start_server()