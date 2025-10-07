from dotenv import load_dotenv
import os

load_dotenv(".env.dev")

class Settings:
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_NAME = os.getenv("DB_NAME")
    DB_SSL_CA = os.getenv("DB_SSL_CA")
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
    
    GOOGLE_TOKEN_ENDPOINT = os.getenv("GOOGLE_TOKEN_ENDPOINT")
    GOOGLE_OAUTH_URI = os.getenv("GOOGLE_OAUTH_URI")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    GOOGLE_OAUTH_ENDPOINT = os.getenv("GOOGLE_OAUTH_ENDPOINT")
    GOOGLE_OAUTH_USERINFO = os.getenv("GOOGLE_OAUTH_USERINFO")
    
    
    APP_REDIRECT_URI = os.getenv("APP_REDIRECT_URI")
    APP_URL_API = os.getenv("APP_URL_API")
    APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_EXPIRE_IN_MINUTES = os.getenv("JWT_EXPIRE_IN_MINUTES")
    
    SSL_KEYFILE = os.getenv("SSL_KEYFILE")
    SSL_CERTFILE = os.getenv("SSL_CERTFILE")

settings = Settings()
