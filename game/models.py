import string, random, time
from config import GameRules
from utils.logger import logger

class Question:
    """
    מחלקה שמייצגת שאלה בחידון
    """
    def __init__(self, question_text : str, option1 : str, option2 : str, option3 : str, option4 : str, correct_option_number : int):
        self._question_text = question_text
        self._options = [option1, option2, option3, option4]
        self._correct_option_number = correct_option_number

    def get_correct_answer_text(self) -> str:
        return self._options[self._correct_option_number - 1]

    @property
    def question_text(self):
        return self._question_text

    def check_answer(self, option_number : int) -> bool:
        """
        בודקת האם התשובה נכונה
        מקבלת קלט של אופציה בחירה מ1-4 
        מחזירה אמת או שקר על הבדיקה
        """
        return int(option_number) == self._correct_option_number

    def to_dict_client(self):
        """
        מחזירה שאלה בתור מילון המוכן לשליחה בסוקט והצגה
        """
        return {
            "question_text": self._question_text,
            "options": [{"id": i+1, "text": opt} for i, opt in enumerate(self._options)]
        }

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
        self._round_start_time = time.time

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
    
    def set_player_inactive(self, player_name):
        """מסמן שחקן כלא פעיל במהלך משחק"""
        if player_name in self._active_players_status:
            self._active_players_status[player_name] = False

    def remove_player_waiting(self, player_name):
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

class RoomManager:
    """
    מחלקה האחראית על כל החדרים הפועלים
    """
    def __init__(self):
        self._active_rooms = {}

    def _generate_unique_code(self):
        """מגריל קוד שעדיין לא קיים במערכת."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            if code not in self._active_rooms:
                return code

    def create_room(self, host_name : str, is_private : bool, max_players : int, num_questions=GameRules.DEFAULT_NUM_QUESTIONS) -> Room:
        """
        יוצרת חדר חדש ומוסיפה אותו לרשימת החדרים
        """
        code = self._generate_unique_code()
        new_room = Room(code, host_name, is_private, max_players, num_questions)
        self._active_rooms[code] = new_room
        return new_room

    def get_room(self, room_code):
        return self._active_rooms.get(room_code)

    def get_public_waiting_rooms(self):
        """מחזיר מילון של כל החדרים הפומביים שממתינים לשחקנים."""
        return {
            code: room.to_dict()
            for code, room in self._active_rooms.items()
            if not room.is_private and room.status == "waiting"
        }