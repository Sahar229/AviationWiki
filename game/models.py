import string, random
from config import GameRules



class Question:
    def __init__(self, question_text, option1, option2, option3, option4, correct_option_number):
        self._question_text = question_text
        self._options = [option1, option2, option3, option4]
        self._correct_option_number = correct_option_number

    def get_correct_answer_text(self):
        return self._options[self._correct_option_number - 1]

    @property
    def question_text(self):
        return self._question_text

    def check_answer(self, option_number):
        return int(option_number) == self._correct_option_number

    def to_dict_client(self):
        return {
            "question_text": self._question_text,
            "options": [{"id": i+1, "text": opt} for i, opt in enumerate(self._options)]
        }

class Room:
    def __init__(self, room_code, host_name, is_private, max_players, num_questions=GameRules.DEFAULT_NUM_QUESTIONS):
        self._code = room_code
        self._host = host_name
        self._players = [host_name]
        self._is_private = is_private
        self._max_players = max_players
        self._num_questions = num_questions
        self._status = "waiting"
        
        # --- Game State ---
        self._questions = []
        self._current_question_idx = 0
        self._scores = {host_name: 0}
        self._total_correct = {host_name: 0}
        self._round_answers = {}
        self._round_start_time = None

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

    # 3. קידום אינדקס השאלה (במקום room.current_question_idx += 1)
    def advance_question(self):
        self._current_question_idx += 1

    # 4. הכנות לסבב חדש (איפוס תשובות ושמירת זמן)
    def start_new_round(self, current_time):
        self._round_answers = {}
        self._round_start_time = current_time

    # 5. קבלת תשובה משחקן
    def register_answer(self, player_name, answer_idx):
        if player_name in self._players:
            self._round_answers[player_name] = answer_idx

    # 6. עדכון ניקוד
    def add_score(self, player_name, points):
        if player_name in self._scores:
            self._scores[player_name] += points

    # 7. עדכון כמות תשובות נכונות
    def increment_total_correct(self, player_name):
        self._total_correct[player_name] += 1


    def add_player(self, player_name):
        """מנסה להוסיף שחקן לחדר. מחזיר True אם הצליח, אחרת מחזיר הודעת שגיאה."""
        if self._status != "waiting":
            return False, "Game already started."
        if len(self._players) >= self._max_players:
            return False, "Room is full."
        if player_name in self._players:
            return False, "You are already in this room."

        self._players.append(player_name)
        self._scores[player_name] = 0
        self._total_correct[player_name] = 0
        return True, "Success"
    

    def to_dict(self):
        """
        ממיר את נתוני החדר למילון כדי שנוכל לשלוח אותו בקלות דרך SocketIO ללקוח (JSON).
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
    def __init__(self):
        self._active_rooms = {}

    def _generate_unique_code(self):
        """מגריל קוד שעדיין לא קיים במערכת."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            if code not in self._active_rooms:
                return code

    def create_room(self, host_name, is_private, max_players, num_questions=10):
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