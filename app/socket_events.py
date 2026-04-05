from flask_socketio import emit, join_room, leave_room
from globals import socketio, game_manager
from flask import session
import game.game_flow as game_flow
import random
from game.questions import AMERICAN_AIRCRAFT_QUESTIONS
from config import GameRules
from utils.logger import logger



@socketio.on('create_room')
def handle_create_room(data):
    """
    פונקציה המטפלת בלחיצת כפתור של יצירת חדר
    """
    user = session.get('username')
    logger.info(f"|socket_events.py| Payload for creating a room received: {data}")

    try:
        #קליטת נתונים
        max_p = int(data.get('max_players', GameRules.DEFAULT_MAX_PLAYERS))
        is_p = data.get('is_private', False)
        num_q = int(data.get('num_questions', GameRules.DEFAULT_NUM_QUESTIONS))
        
        #יצירת חדר
        new_room = game_manager.create_room(user, is_p, max_p, num_q)
        logger.info(f"|socket_events.py| Room Created in Memory: {new_room.code}")
        
        join_room(new_room.code)
        
        logger.info(f"|socket_events.py| Emitting 'room_created' for room {new_room.code}")
        emit('room_created', {'room_code': new_room.code, 'room_data': new_room.to_dict()})

        if not is_p:
            broadcast_public_rooms()
    except Exception as e:
        logger.exception("|socket_events.py| Error in creating a room")


@socketio.on('join_room_request')
def handle_join_room(data):
    """
    פונקציה המטפלת בהכנסת שחקן לחדר לאחר לחיצה על כפתור הכניסה
    """
    try:
        room_code = data.get('room_code', '').upper()
        username = session.get('username')
        
        room = game_manager.get_room(room_code)
        
        if not room:
            emit('join_error', {'message': 'Room not found.'})
            logger.warning("|socket_events.py| tried to join non exisiting room")
            return
            
        # מנסים להוסיף את השחקן למחלקת החדר
        success, message = room.add_player(username)
        
        if not success:
            emit('join_error', {'message': message})
            logger.error("|socket_events.py| error while trying to join room")
            return
            
        # הכל תקין
        logger.info(f"|socket_events.py| {username} joined to room {room_code}")
        join_room(room_code)
        emit('room_joined', {'room_code': room_code, 'room_data': room.to_dict()})
        emit('player_joined', {'username': username, 'room_data': room.to_dict()}, to=room_code)

        
        broadcast_public_rooms()
    except Exception as e:
        logger.exception("|socket_events.py| Error in joining room")



@socketio.on('get_public_rooms')
def handle_get_public_rooms():
    """
    פוקנציה המטפלת בקריאה להציג את כל החדרים הפתוחים
    """
    broadcast_public_rooms()


def broadcast_public_rooms():
    """
    פונקציה המציגה את כל החדרים הפתוחים
    """
    try:
        public_rooms = game_manager.get_public_waiting_rooms()
        socketio.emit('public_rooms_update', public_rooms)
    except Exception as e:
        logger.exception("|socket_events.py| Error in brodcasting public rooms")

@socketio.on('join_room_socket')
def handle_join_room_socket(data):
    """
    נקרא כשהעמוד של חדר ההמתנה נטען.
    מצרף את חיבור הסוקט החדש של המשתמש לחדר הוירטואלי, ומשדר לכולם את רשימת השחקנים.
    """
    try:
        room_code = data.get('room_code')
        room = game_manager.get_room(room_code)
        
        if room:
            # צירוף הסוקט לחדר
            join_room(room_code)
            # שידור רשימת השחקנים המעודכנת לכל מי שבחדר
            emit('update_players', {'players': room.players}, to=room_code)
    except Exception as e:
        logger.exception("|socket_events.py| Error in joining room socket")


@socketio.on('start_game_request')
def handle_start_game(data):
    """
    מטפל כאשר המארח לחץ על כפתור התחלת המשחק, מתחיל את המשחק
    """
    try:
        room_code = data.get('room_code')
        username = session.get('username')
        
        room = game_manager.get_room(room_code)
        if not room or room.host != username or room.status != "waiting":
            return
        if len(room.players) < GameRules.MIN_PLAYERS:
            emit('not_enough_players', {}, to=room_code)
            return
            
        room.status = "playing"
        try:
            room.questions = random.sample(AMERICAN_AIRCRAFT_QUESTIONS, room.num_questions)
        except ValueError:
            room.questions = AMERICAN_AIRCRAFT_QUESTIONS

        broadcast_public_rooms()
        emit('game_started', {}, to=room_code)
        logger.info(f"|socket_events.py| starting game in room {room_code}")
        #קריאה לסיבוב הבא - הראשון
        def initial_start_task():
            """
            פונקציה פנימית להשהיית הלחיצה לפני התחלת החידון
            """
            socketio.sleep(GameRules.GAME_START_DELAY)
            game_flow.start_next_round(room_code)
        socketio.start_background_task(initial_start_task)
    except Exception as e:
        logger.exception("|socket_events.py| Error in starting game")



@socketio.on('submit_answer')
def handle_submit_answer(data):
    """
    מנהל את הגשת התשובה כל סבב
    """
    try:
        room_code = data.get('room_code')
        answer_idx = data.get('answer_idx')
        username = session.get('username')
        
        room = game_manager.get_room(room_code)
        if not room or room.status != "playing": return
        if username not in room.players or username in room.round_answers: return
        
        #בדיקה ורשימה של התשובה של המשתמש
        q = room.questions[room.current_question_idx]
        is_correct = q.check_answer(answer_idx)
        room.register_answer(username,answer_idx)
        
        #מערכת נקודות
        points_awarded = 0
        if is_correct:
            room.increment_total_correct(username)
            
            correct_count_this_round = 0
            for p, a in room.round_answers.items():
                if p != username and q.check_answer(a):
                    correct_count_this_round += 1                
            points_awarded = (GameRules.BASE_POINTS - (GameRules.PENALTY_PER_OTHER_CORRECT * correct_count_this_round))
            
        room.add_score(username, points_awarded)
        
        #בדיקה האם כולם ענו
        if len(room.round_answers) == len(room.players):
            socketio.start_background_task(game_flow.end_round, room_code, room.current_question_idx)
    except Exception as e:
        logger.exception("|socket_events.py| Error in submitting answer")
