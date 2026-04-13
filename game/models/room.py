import time
from config import GameRules
from utils.logger import logger
from .question import Question

class Room:
    """
    מחלקה המייצגת חדר משחק
    """
    def __init__(self, room_code : str, host_name : str, is_private : bool, max_players : int, num_questions=GameRules.DEFAULT_NUM_QUESTIONS):
        #נתוני חדר
        self._code = room_code
        self._host = host_name
        self._players = [host_name]
        self._is_private = is_private
        self._max_players = max_players
        self._num_questions = num_questions
        self._status = "waiting"
        self._active_players_status = {host_name: True}
        
        # נתוני משחק
        self._questions = []
        self._current_question_idx = 0
        self._scores = {host_name: 0}
        self._total_correct = {host_name: 0}
        self._round_answers = {}
        self._round_start_time = None
        self._errors = {}


    #גטים וסטים
    
    @property
    def code(self): return self._code
    
    @property
    def host(self): return self._host
    
    @property
    def players(self): return self._players.copy()

    @property
    def is_private(self): return self._is_private

    @property
    def max_players(self): return self._max_players

    @property
    def num_questions(self): return self._num_questions

    @property
    def status(self): return self._status

    @property
    def active_players_status(self): return self._active_players_status.copy()

    @property
    def questions(self): return self._questions

    @property
    def current_question_idx(self): return self._current_question_idx

    @property
    def scores(self): return self._scores.copy()

    @property
    def total_correct(self): return self._total_correct.copy()

    @property
    def round_answers(self): return self._round_answers.copy()

    @property
    def round_start_time(self): return self._round_start_time

    @property
    def errors(self): return self._errors


    @status.setter
    def status(self, new_status):
        if new_status in ["waiting", "playing", "finished"]:
            self._status = new_status
    
    @round_start_time.setter
    def round_start_time(self, new_status):
        self._round_start_time = new_status

    @questions.setter
    def questions(self, selected_questions):
        self._questions = selected_questions

    
    #פעולות חיוניות למשחק
    
    def advance_question(self):
        """
        מקדמת את המשחק בשאלה
        """
        self._current_question_idx += 1

    def start_new_round(self):
        """
        מתחילה ראונד חדש
        מאפסת את רשימת התשובות של המשתמש ורושמת את הזמן שהביאו לה כקלט
        """
        self._round_answers = {}
        self._round_start_time = time.time()

    def register_answer(self, player_name : str, answer_idx : int):
        """
        רושמת במילון לכל שחקן את התשובה שלו
        """
        if player_name in self._players:
            self._round_answers[player_name] = answer_idx

    def add_score(self, player_name : str, points : int):
        """
        מוסיפה לכל שחקן את הניקוד שלו
        """
        if player_name in self._scores:
            self._scores[player_name] += points

    def increment_total_correct(self, player_name : str):
        """
        מקדמת את מספר התשובות הנכונות של שחקן
        """
        self._total_correct[player_name] += 1

    def get_active_players_count(self):
        """מחזיר את כמות השחקנים שעדיין מחוברים למשחק"""
        return sum(1 for status in self._active_players_status.values() if status)
    
    def set_player_inactive(self, player_name : str):
        """מסמן שחקן כלא פעיל במהלך משחק"""
        if player_name in self._active_players_status:
            self._active_players_status[player_name] = False

    def remove_player_waiting(self, player_name : str):
        """מוחק שחקן מהחדר (מיועד רק למצב המתנה). מחזיר אמת אם החדר התרוקן."""
        if player_name in self._players:
            self._players.remove(player_name)
            if player_name in self._scores: del self._scores[player_name]
            if player_name in self._total_correct: del self._total_correct[player_name]
            if player_name in self._active_players_status: del self._active_players_status[player_name]
        logger.info(f"|models.py| removing {player_name} from room {self._code}")
        return len(self._players) == 0

    def reassign_host(self):
        """מעביר את האירוח לשחקן הראשון ברשימה (אם יש כזה)"""
        if len(self._players) > 0:
            self._host = self._players[0]
            return self._host
        return None
    

    def record_error(self, username : str, question_text : str, user_answer : str, correct_answer : str):
        # אם זו הטעות הראשונה של המשתמש ניצור רשימה ריקה
        if username not in self._errors:
            self._errors[username] = []
            
        # נוסיף את הטעות החדשה לרשימה שלו
        mistake = {
            "question": question_text,
            "user_answer": user_answer,
            "correct_answer": correct_answer
        }
        self._errors[username].append(mistake)


    def add_player(self, player_name : str):
        """מנסה להוסיף שחקן לחדר. מחזיר אמת אם הצליח, אחרת מחזיר הודעת שגיאה."""
        if self._status != "waiting":
            logger.warning(f"|models.py| {player_name} tried to join a game that already started in room {self._code}")
            return False, "Game already started."
        if len(self._players) >= self._max_players:
            logger.warning(f"|models.py| {player_name} tried to join a full room {self._code}")
            return False, "Room is full."
        if player_name in self._players:
            logger.warning(f"|models.py| {player_name} is already in room {self._code}")
            return False, "You are already in this room."

        self._players.append(player_name)
        self._scores[player_name] = 0
        self._total_correct[player_name] = 0
        self._active_players_status[player_name] = True
        logger.info(f"|models.py| added {player_name} to room {self._code}")
        return True, "Success"
    

    def to_dict(self):
        """
        ממיר את נתוני החדר למילון כדי שנוכל לשלוח אותו בקלות דרך סוקט ללקוח.
        """
        return {
            "code": self._code,
            "host": self._host,
            "players": self._players,
            "is_private": self._is_private,
            "max_players": self._max_players,
            "num_questions": self._num_questions,
            "status": self._status
        }
    