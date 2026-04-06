from config import GameRules
from globals import socketio, game_manager, db_req
from utils.logger import logger


def start_next_round(room_code):
    """
    פונקציה הדואגת להתחיל את הסבב הבא אצל כולם
    """
    try:
        room = game_manager.get_room(room_code)
        if not room or room.status != "playing": return
        
        #בדיקת סיבוב אחרון - סיום משחק
        if room.current_question_idx >= room.num_questions or room.current_question_idx >= len(room.questions):
            end_game(room_code)
            return
            
        q = room.questions[room.current_question_idx]
        
        #שליחת השאלה החדשה
        socketio.emit('start_round', {
            'question_number': room.current_question_idx + 1,
            'total_questions': room.num_questions,
            'question': q.to_dict_client(),
            'duration': GameRules.QUESTION_TIMER
        }, to=room_code)
        
        #שינוי הגדרות החדר
        room.start_new_round()
    
        def timer_task(question_idx):
            """
            פונקציה פנימית שאחראית על טיימר של השאלה
            """
            socketio.sleep(GameRules.QUESTION_TIMER)
            current_room = game_manager.get_room(room_code)
            if current_room and current_room.status == "playing":
                if current_room.current_question_idx == question_idx:
                    end_round(room_code, question_idx)

        socketio.start_background_task(timer_task, room.current_question_idx)

    except Exception as e:
        logger.exception("|game_flow.py| Error in starting the next round")


def end_round(room_code, question_idx):
    """
    פונקציה שאחראית על סיום הסבב ועדכון התוצאות
    """
    try:
        #בדיקות אמינות
        room = game_manager.get_room(room_code)
        if not room or room.status != "playing": return
        if room.current_question_idx != question_idx: return
        
        q = room.questions[room.current_question_idx]
        
        #בדיקת מצב של כל שחקן
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
                
        #הבאת תשובה נכונה
        correct_text = q.get_correct_answer_text()
        
        #שליחת מסך תוצאות לחדר
        socketio.emit('round_results', {
            'correct_answer': correct_text,
            'results': results,
            'scores': room.scores
        }, to=room_code)
        
        #קידום שאלה
        room.advance_question()
        
        def next_round_task():
            """
            פונקציה פנימית שמשהה לפני הסיבוב הבא
            """
            socketio.sleep(GameRules.ROUND_TRANSITION_DELAY)
            start_next_round(room_code)
            
        socketio.start_background_task(next_round_task)
    except Exception as e:
        logger.exception("|game_flow.py| Error in ending the round")

def end_game(room_code):
    """
    פונקציה שאחראית על סיום המשחק וסיכומו
    """
    try:
        #בדיקות אמינות
        room = game_manager.get_room(room_code)
        if not room: return
        room.status = "finished"
        
        #בדיקת מנצחים
        sorted_players = sorted(room.scores.items(), key=lambda x: x[1], reverse=True)
        max_score = sorted_players[0][1] if sorted_players else None
        
        # הלוגיקה החדשה: מנצח קיים רק אם הציון הגבוה ביותר הוא מעל 0
        if max_score is not None and max_score > 0:
            winner_names = [p[0] for p in sorted_players if p[1] == max_score]
        else:
            # אם הציון הכי גבוה הוא 0 (או פחות), הרשימה נשארת ריקה - אין מנצחים!
            winner_names = []
        
        #שליחת נתונים למסד נתונים
        for player_name in room.players:
            won = (player_name in winner_names)
            correct_count = room.total_correct.get(player_name, 0)
            db_req.send_request("UPDATE_STATS_REQUEST", {
                "username": player_name,
                "won": won,
                "correct_count": correct_count
            })
            
        #הודעת סיום משחק
        socketio.emit('game_over', {
            'standings': [{"name": p, "score": s} for p, s in sorted_players],
            'winners': winner_names
        }, to=room_code)
    except Exception as e:
        logger.exception("|game_flow.py| Error in ending the game")
