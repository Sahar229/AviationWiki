import string, random
from config import GameRules
from .room import Room


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
    