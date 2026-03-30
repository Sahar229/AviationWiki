import string, random

class Room:
    def __init__(self, room_code, host_name, is_private, max_players):
        self.code = room_code
        self.host = host_name
        self.players = [host_name]  # המארח נכנס אוטומטית כראשון
        self.is_private = is_private
        self.max_players = max_players
        self.status = "waiting"     # יכול להיות: waiting, playing, finished

    def add_player(self, player_name):
        """מנסה להוסיף שחקן לחדר. מחזיר True אם הצליח, אחרת מחזיר הודעת שגיאה."""
        if self.status != "waiting":
            return False, "Game already started."
        if len(self.players) >= self.max_players:
            return False, "Room is full."
        if player_name in self.players:
            return False, "You are already in this room."
        
        self.players.append(player_name)
        return True, "Success"

    def to_dict(self):
        """
        ממיר את נתוני החדר למילון כדי שנוכל לשלוח אותו בקלות דרך SocketIO ללקוח (JSON).
        """
        return {
            "code": self.code,
            "host": self.host,
            "players": self.players,
            "is_private": self.is_private,
            "max_players": self.max_players,
            "status": self.status
        }

class RoomManager:
    def __init__(self):
        self.active_rooms = {}

    def generate_unique_code(self):
        """מגריל קוד שעדיין לא קיים במערכת."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            if code not in self.active_rooms:
                return code

    def create_room(self, host_name, is_private, max_players):
        code = self.generate_unique_code()
        new_room = Room(code, host_name, is_private, max_players)
        self.active_rooms[code] = new_room
        return new_room

    def get_room(self, room_code):
        return self.active_rooms.get(room_code)

    def get_public_waiting_rooms(self):
        """מחזיר מילון של כל החדרים הפומביים שממתינים לשחקנים."""
        return {
            code: room.to_dict()
            for code, room in self.active_rooms.items()
            if not room.is_private and room.status == "waiting"
        }