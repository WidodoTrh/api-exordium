from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from fastapi import HTTPException
import base64

def decrypt_password(encrypted_password: str):
    try:
        with open('app/keys/private.pem', 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
            )
        decrypted = private_key.decrypt(
            base64.b64decode(encrypted_password),
            padding.PKCS1v15()
        )
        return decrypted.decode('utf-8')
    except Exception as e:
        print("decrypt error:", e)
        raise HTTPException(status_code=400, detail="Invalid encrypted password")
