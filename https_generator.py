#create ssl permissions
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime

def generate_self_signed_cert():
    # 1. יצירת מפתח פרטי (Private Key)
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # 2. יצירת פרטי "החברה" (במקרה הזה - המחשב שלך)
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"IL"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Tel Aviv"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Ramat Gan"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Aviation Wiki Project"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"127.0.0.1"),
    ])

    # 3. יצירת התעודה עצמה (Certificate)
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        subject # חתימה עצמית - אנחנו גם המנפיק וגם הנושא
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        # התעודה תהיה תקפה לשנה (365 ימים)
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(key, hashes.SHA256())

    # 4. שמירת קובץ המפתח (key.pem)
    with open("key.pem", "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    # 5. שמירת קובץ התעודה (cert.pem)
    with open("cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print("Success! Created cert.pem and key.pem")

if __name__ == "__main__":
    generate_self_signed_cert()