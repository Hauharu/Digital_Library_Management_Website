import os
from dotenv import load_dotenv
import stripe
from urllib.parse import quote_plus
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', '12b23b02a8ceeb2cf3386bb33d4d8f31')
    
    _db_user = os.getenv('DB_USER', 'root')
    _db_pass = quote_plus(os.getenv('DB_PASSWORD', 'admin'))
    _db_host = os.getenv('DB_HOST', 'localhost')
    _db_port = os.getenv('DB_PORT', '3306')
    _db_name = os.getenv('DB_NAME', 'thu_vien_so')
    
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI',
        f'mysql+pymysql://{_db_user}:{_db_pass}@{_db_host}:{_db_port}/{_db_name}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')


    GOOGLE_OAUTH_CONFIG = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'access_token_url': 'https://oauth2.googleapis.com/token',
        'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
        'api_base_url': 'https://www.googleapis.com/oauth2/v1/',
        'client_kwargs': {'scope': 'openid email profile'},
        'server_metadata_url': 'https://accounts.google.com/.well-known/openid-configuration',
        "redirect_uri": "http://127.0.0.1:5000/auth/google/callback"
    }


    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

