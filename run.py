import threading

import app.routes as routes
import app.socket_events as socket_events
from globals import app, socketio
from config import ServerConfig
from database.db_server import DatabaseServer
from utils.logger import logger


def start_database_server():
    """
    פונקציית עזר לפתיחת טרד של השרת של בסיס הנתונים
    """
    db_ser = DatabaseServer()
    db_ser.start_server()
    logger.info("|run.py| Starting DB Server thread")


if __name__ == "__main__":
    db_thread = threading.Thread(target=start_database_server, daemon=True)
    db_thread.start()
    
    # הפעלת שרת
    socketio.run(app, 
                 debug=True, 
                 port=ServerConfig.PORT, 
                 certfile=ServerConfig.CERT_FILE, 
                 keyfile=ServerConfig.KEY_FILE,
                 use_reloader=False)
    
    logger.info("|run.py| starting main server")
