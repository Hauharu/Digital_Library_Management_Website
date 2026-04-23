from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
import cloudinary




db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
socketio = SocketIO(cors_allowed_origins="*")
migrate = Migrate()
mail = Mail()
oauth = OAuth()


def create_app(config_name=None):
    app = Flask(__name__)

    if config_name == 'testing':
        app.config.from_object('app.config.TestingConfig')
    elif config_name:
        app.config.from_object(f"app.config.{config_name.capitalize()}Config")
    else:
        app.config.from_object("app.config.Config")

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.login_message = "Vui lòng đăng nhập để tiếp tục."

    bcrypt.init_app(app)
    socketio.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    oauth.init_app(app)

    CORS(app)

    # Cloudinary Config
    cloudinary.config(
        cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=app.config['CLOUDINARY_API_KEY'],
        api_secret=app.config['CLOUDINARY_API_SECRET'],
        secure=True
    )

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    google_config = app.config.get('GOOGLE_OAUTH_CONFIG')
    if google_config:
        oauth.register(
            name='google',
            **google_config
        )

    from app.routes.auth_routes import auth_bp
    from app.routes.main_routes import main_bp
    from app.routes.user_routes import user_bp
    from app.routes.admin_routes import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    @app.template_filter('time_ago')
    def time_ago_filter(dt):
        if not dt:
            return ""
        from datetime import datetime
        now = datetime.now()
        diff = now - dt
        
        seconds = diff.total_seconds()
        if seconds < 60:
            return f"{int(seconds)} giây trước"
        minutes = seconds // 60
        if minutes < 60:
            return f"{int(minutes)} phút trước"
        hours = minutes // 60
        if hours < 24:
            return f"{int(hours)} giờ trước"
        days = hours // 24
        if days < 30:
            return f"{int(days)} ngày trước"
        months = days // 30
        if months < 12:
            return f"{int(months)} tháng trước"
        years = days // 365
        return f"{int(years)} năm trước"

    from app import models

    with app.app_context():
        db.create_all()

    @app.context_processor
    def inject_notifications():
        from app.models import Notification
        from flask_login import current_user
        if current_user.is_authenticated:
            # Lấy 5 thông báo mới nhất
            notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.sent_date.desc()).limit(5).all()
            unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            return dict(notifications=notifications, unread_count=unread_count)
        return dict(notifications=[], unread_count=0)

    return app

# ================= SOCKET.IO EVENTS =================
from flask_socketio import join_room, emit
from flask_login import current_user
from datetime import datetime

@socketio.on('join')
def on_join(data):
    room = f"book_{data['book_id']}"
    join_room(room)

@socketio.on('send_message')
def handle_message(data):
    if not current_user.is_authenticated:
        return
        
    from app.models import Message, Book
    from app import db
    
    book_id = data['book_id']
    content = data['message']
    
    # Lưu vào database
    new_msg = Message(
        content=content,
        user_id=current_user.id,
        book_id=book_id,
        sent_date=datetime.now()
    )
    db.session.add(new_msg)
    db.session.commit()
    
    # Gửi lại cho mọi người trong phòng
    room = f"book_{book_id}"
    full_name = f"{(current_user.last_name or '').strip()} {(current_user.first_name or '').strip()}".strip()
    user_name = full_name or current_user.username
    
    emit('receive_message', {
        'message': content,
        'user': user_name,
        'avatar': current_user.avatar,
        'time': datetime.now().strftime('%H:%M'),
        'user_id': current_user.id
    }, room=room)