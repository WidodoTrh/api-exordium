from dotenv import load_dotenv
import os

load_dotenv(".env.dev")

class Settings:
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")
    
    SSL_KEYFILE = os.getenv("SSL_KEYFILE")
    SSL_CERTFILE = os.getenv("SSL_CERTFILE")

settings = Settings()
