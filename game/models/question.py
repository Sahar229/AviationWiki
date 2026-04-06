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
    