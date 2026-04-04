from globals import app, socketio
from config import ServerConfig
from database.db_server import DatabaseServer
import app.routes as routes
import app.socket_events as socket_events
import threading

def start_database_server():
    db_ser = DatabaseServer()
    db_ser.start_server()

if __name__ == "__main__":

    db_thread = threading.Thread(target=start_database_server, daemon=True)
    db_thread.start()

    
    socketio.run(app, 
                 debug=True, 
                 port=ServerConfig.PORT, 
                 certfile=ServerConfig.CERT_FILE, 
                 keyfile=ServerConfig.KEY_FILE,
                 use_reloader=False)