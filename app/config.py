import os
from dotenv import load_dotenv
import stripe
from urllib.parse import quote_plus
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', '12b23b02a8ceeb2cf3386bb33d4d8f31')
    
    # Try MySQL first, fallback to SQLite for testing
    _db_user = os.getenv('DB_USER', 'root')
    _db_pass = quote_plus(os.getenv('DB_PASSWORD', '123456'))
    _db_host = os.getenv('DB_HOST', '127.0.0.1')
    _db_port = os.getenv('DB_PORT', '3306')
    _db_name = os.getenv('DB_NAME', 'library_db')
    
    # Use MySQL by default, SQLite only for testing
    if os.getenv('USE_SQLITE', 'false').lower() == 'true':
        SQLALCHEMY_DATABASE_URI = 'sqlite:///library_test.db'
        print("Using SQLite database for testing")
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv(
            'DATABASE_URI',
            f'mysql+pymysql://root:123456@127.0.0.1:3306/library_db'
        )
        print("Using MySQL database")
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

    VNPAY_TMN_CODE = os.environ.get("VNPAY_TMN_CODE")
    VNPAY_HASH_SECRET = os.environ.get("VNPAY_HASH_SECRET")
    VNPAY_PAYMENT_URL = os.environ.get("VNPAY_PAYMENT_URL")
    VNPAY_RETURN_URL = os.environ.get("VNPAY_RETURN_URL")

    PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
    PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET")

