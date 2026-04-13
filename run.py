import threading

from flask import request, session, redirect, url_for

import app.socket_events as socket_events
from globals import app, socketio, active_sessions
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


@app.before_request
def check_valid_login():
    """
    פונקציה המוחקת סשן של משתמש אם הוא לא הנוכחי
    שומרת על עקרון של התחברות יחידה
    """
    # לא נבדוק נתיבים שקשורים להתחברות עצמה או לקבצים סטטיים כדי לא ליצור לולאה אינסופית
    if request.endpoint and request.endpoint not in ['auth.login_page', 'static']:
        username = session.get('username')
        user_token = session.get('login_token')

        if username:
            server_valid_token = active_sessions.get(username)
            if server_valid_token != user_token:
                logger.warning(f"|run.py| {username} tried to do an action while connected from somewhere else")
                session.clear()
                return redirect(url_for('auth.login_page'))

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

