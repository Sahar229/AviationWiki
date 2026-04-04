from globals import socketio, game_manager, db_req
import time
from config import GameRules


def start_next_round(room_code):
    room = game_manager.get_room(room_code)
    if not room or room.status != "playing": return
    
    if room.current_question_idx >= room.num_questions or room.current_question_idx >= len(room.questions):
        end_game(room_code)
        return
        
    q = room.questions[room.current_question_idx]
    
    socketio.emit('start_round', {
        'question_number': room.current_question_idx + 1,
        'total_questions': room.num_questions,
        'question': q.to_dict_client(),
        'duration': GameRules.QUESTION_TIMER
    }, to=room_code)
    
    room.start_new_round(time.time)
    
    def timer_task(question_idx):
        socketio.sleep(GameRules.QUESTION_TIMER)
        current_room = game_manager.get_room(room_code)
        if current_room and current_room.status == "playing":
            if current_room.current_question_idx == question_idx:
                end_round(room_code, question_idx)

    socketio.start_background_task(timer_task, room.current_question_idx)


def end_round(room_code, question_idx):
    room = game_manager.get_room(room_code)
    if not room or room.status != "playing": return
    if room.current_question_idx != question_idx: return
    
    q = room.questions[room.current_question_idx]
    
    results = {}
    for player in room.players:
        if player in room.round_answers:
            player_ans = room.round_answers[player]
            is_correct = q.check_answer(player_ans)
            results[player] = {
                "answered": True,
                "correct": is_correct
            }
        else:
            results[player] = {"answered": False, "correct": False}
             
    correct_text = q.get_correct_answer_text()
    
    socketio.emit('round_results', {
        'correct_answer': correct_text,
        'results': results,
        'scores': room.scores
    }, to=room_code)
    
    room.advance_question()
    
    def next_round_task():
        socketio.sleep(GameRules.ROUND_TRANSITION_DELAY)
        start_next_round(room_code)
        
    socketio.start_background_task(next_round_task)

def end_game(room_code):
    room = game_manager.get_room(room_code)
    if not room: return
    room.status = "finished"
    
    sorted_players = sorted(room.scores.items(), key=lambda x: x[1], reverse=True)
    max_score = sorted_players[0][1] if sorted_players else None
    winner_names = [p[0] for p in sorted_players if p[1] == max_score] if sorted_players else []
    
    for player_name in room.players:
        won = (player_name in winner_names)
        correct_count = room.total_correct.get(player_name, 0)
        db_req.send_request("UPDATE_STATS_REQUEST", {
            "username": player_name,
            "won": won,
            "correct_count": correct_count
        })
         
    socketio.emit('game_over', {
        'standings': [{"name": p, "score": s} for p, s in sorted_players],
        'winners': winner_names
    }, to=room_code)
