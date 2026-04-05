from flask import Flask
from flask_socketio import SocketIO
from game.models import RoomManager
from database.db_client import DatabaseClient
from config import ServerConfig
from config import DBConfig
import os
from utils.logger import logger


#פתיחת הפלאסק
base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'app', 'templates'),
            static_folder=os.path.join(base_dir, 'app', 'static'))
app.secret_key = ServerConfig.SECRET_KEY
socketio = SocketIO(app)

# מנהל המשחק ושרת מסד הנתונים שחיים בזיכרון
game_manager = RoomManager()
db_req = DatabaseClient(DBConfig.HOST2,DBConfig.PORT)

logger.info("|globals.py| created all of the global instances")