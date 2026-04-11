import hashlib
from diffiehellman import DiffieHellman
from Crypto.Cipher import AES
import base64

class NetworkCipher:
    """
    מחלקה הדואגת ללחיצת יד ושיתוף מפתחות על פי AES
    """
    def __init__(self, shared_key=None):
        self._shared_key = shared_key

    @staticmethod
    def generate_dh_keys():
        """מייצר אובייקט DH ומפתח ציבורי לשיתוף"""
        dh = DiffieHellman(group=14, key_bits=540)
        pub_key = dh.get_public_key()
        if isinstance(pub_key, bytes):
            # אנחנו מוסיפים קידומת "B64:" כדי שנדע בצד השני שזה עבר המרה
            pub_key = "B64:" + base64.b64encode(pub_key).decode('utf-8')
        return dh, pub_key

    @staticmethod
    def compute_shared_key(dh_instance, peer_public_key):
        """מחשב את הסוד המשותף ומחזיר אותו כמפתח AES תקני"""
        if isinstance(peer_public_key, str) and peer_public_key.startswith("B64:"):
            peer_public_key = base64.b64decode(peer_public_key[4:])
        shared_secret = dh_instance.generate_shared_key(peer_public_key)
        return shared_secret[:32].encode('utf-8') if isinstance(shared_secret, str) else shared_secret[:32]

    def aes_encrypt(self, data: str) -> tuple:
        """מצפין טקסט ומחזיר (ciphertext, nonce, tag)"""
        cipher = AES.new(self._shared_key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(data.encode('utf-8'))
        return ciphertext, cipher.nonce, tag

    def aes_decrypt(self, ciphertext, nonce, tag) -> str:
        """מפענח טקסט מוצפן"""
        cipher = AES.new(self._shared_key, AES.MODE_EAX, nonce=nonce)
        data = cipher.decrypt_and_verify(ciphertext, tag)
        return data.decode('utf-8')


def hash_password(password: str) -> str:
    """
    פונקציית עזר להצפנת סיסמה. מקבלת סיסמה כטקסט גלוי ומחזירה אותה מוצפנת.
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()
