from flask_socketio import emit, join_room, leave_room
from globals import socketio, game_manager
from flask import session
import game.game_flow as game_flow
import random
from game.questions import AMERICAN_AIRCRAFT_QUESTIONS
from config import GameRules



@socketio.on('create_room')
def handle_create_room(data):
    user = session.get('username')
    # logger.info(f"--- [START CREATE_ROOM] --- User: {user}")
    # logger.info(f"Payload received: {data}")

    try:
        max_p = int(data.get('max_players', GameRules.DEFAULT_MAX_PLAYERS))
        is_p = data.get('is_private', False)
        num_q = int(data.get('num_questions', GameRules.DEFAULT_NUM_QUESTIONS))
        
        new_room = game_manager.create_room(user, is_p, max_p, num_q)
        # logger.info(f"Room Created in Memory: {new_room.code}")
        
        join_room(new_room.code)
        
        # הלוג הקריטי - האם שלחנו את האישור?
        # logger.info(f"Emitting 'room_created' for room {new_room.code}")
        emit('room_created', {'room_code': new_room.code, 'room_data': new_room.to_dict()})

        if not is_p:
            broadcast_public_rooms()
    except Exception as e:
        print(f"Error: {e}")


@socketio.on('join_room_request')
def handle_join_room(data):
    room_code = data.get('room_code', '').upper()
    username = session.get('username')
    
    room = game_manager.get_room(room_code)
    
    if not room:
        emit('join_error', {'message': 'Room not found.'})
        return
        
    # מנסים להוסיף את השחקן למחלקת החדר
    success, message = room.add_player(username)
    
    if not success:
        emit('join_error', {'message': message})
        return
        
    # הכל תקין
    join_room(room_code)
    emit('room_joined', {'room_code': room_code, 'room_data': room.to_dict()})
    emit('player_joined', {'username': username, 'room_data': room.to_dict()}, to=room_code)
    
    broadcast_public_rooms()


@socketio.on('get_public_rooms')
def handle_get_public_rooms():
    broadcast_public_rooms()


def broadcast_public_rooms():
    # פשוט קוראים לפונקציה של ה-Manager ומשדרים את התוצאה
    public_rooms = game_manager.get_public_waiting_rooms()
    socketio.emit('public_rooms_update', public_rooms)

@socketio.on('join_room_socket')
def handle_join_room_socket(data):
    """
    נקרא כשהעמוד של חדר ההמתנה נטען.
    מצרף את חיבור הסוקט החדש של המשתמש לחדר הוירטואלי, ומשדר לכולם את רשימת השחקנים.
    """
    room_code = data.get('room_code')
    room = game_manager.get_room(room_code)
    
    if room:
        # צירוף הסוקט לחדר
        join_room(room_code)
        # שידור רשימת השחקנים המעודכנת לכל מי שבחדר
        emit('update_players', {'players': room.players}, to=room_code)


@socketio.on('start_game_request')
def handle_start_game(data):
    room_code = data.get('room_code')
    username = session.get('username')
    
    room = game_manager.get_room(room_code)
    if not room or room.host != username or room.status != "waiting":
        return
        
    room.status = "playing"
    try:
        room.questions = random.sample(AMERICAN_AIRCRAFT_QUESTIONS, room.num_questions)
    except ValueError:
        room.questions = AMERICAN_AIRCRAFT_QUESTIONS
    # room.current_question_idx = 0
    
    # for p in room.players:
    #     room.scores[p] = 0
    #     room.total_correct[p] = 0
        
    broadcast_public_rooms()
    emit('game_started', {}, to=room_code)
    
    def initial_start_task():
        socketio.sleep(3)
        game_flow.start_next_round(room_code)
    socketio.start_background_task(initial_start_task)



@socketio.on('submit_answer')
def handle_submit_answer(data):
    room_code = data.get('room_code')
    answer_idx = data.get('answer_idx')
    username = session.get('username')
    
    room = game_manager.get_room(room_code)
    if not room or room.status != "playing": return
    if username not in room.players or username in room.round_answers: return
        
    q = room.questions[room.current_question_idx]
    is_correct = q.check_answer(answer_idx)
    room.register_answer(username,answer_idx)
    
    points_awarded = 0
    if is_correct:
        room.increment_total_correct(username)
         
        correct_count_this_round = 0
        for p, a in room.round_answers.items():
            if p != username and q.check_answer(a):
                correct_count_this_round += 1                
        points_awarded = (GameRules.BASE_POINTS - (GameRules.PENALTY_PER_OTHER_CORRECT * correct_count_this_round))
         
    room.add_score(username, points_awarded)
    
    if len(room.round_answers) == len(room.players):
        # We must cancel the background sleep if possible, but since we check state, 
        # it is safer to just trigger it via background task directly:
        socketio.start_background_task(game_flow.end_round, room_code, room.current_question_idx)