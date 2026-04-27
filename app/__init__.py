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
socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')
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
    from app.routes.staff_routes import staff_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)

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

    @app.context_processor
    def inject_recent_discussions():
        from app.models import Review
        # Lấy 5 bình luận/đánh giá mới nhất trên toàn hệ thống
        recent = Review.query.order_by(Review.created_at.desc()).limit(5).all()
        # Đếm số lượng bình luận chưa đọc thực tế
        unread_reviews_count = Review.query.filter_by(is_read=False).count()
        return dict(recent_discussions=recent, unread_reviews_count=unread_reviews_count)

    return app

# ================= SOCKET.IO EVENTS =================
from flask_socketio import join_room, emit
from flask_login import current_user
from datetime import datetime

@socketio.on('join')
def on_join(data):
    room = f"book_{data['book_id']}"
    join_room(room)

@socketio.on('join_user')
def on_join_user(data):
    if current_user.is_authenticated:
        room = f"user_{current_user.id}"
        join_room(room)

@socketio.on('send_message')
def handle_message(data):
    if not current_user.is_authenticated:
        return
        
    from app.models import Review, Book, ReviewLike, ReviewReply
    from app import db
    
    book_id = data['book_id']
    content = data.get('message')
    rating = data.get('rating') 
    
    try:
        # Kiểm tra xem user đã đánh giá cuốn sách này chưa
        existing_rev = Review.query.filter_by(user_id=current_user.id, book_id=book_id).first()
        
        if existing_rev:
            existing_rev.content = content
            existing_rev.rating = rating
            existing_rev.created_at = datetime.now()
            db.session.commit()
            msg_id = existing_rev.id
        else:
            new_rev = Review(
                content=content,
                rating=rating,
                user_id=current_user.id,
                book_id=book_id,
                created_at=datetime.now()
            )
            db.session.add(new_rev)
            db.session.commit()
            msg_id = new_rev.id
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi DB: {str(e)}")
        return
    
    room = f"book_{book_id}"
    full_name = f"{(current_user.last_name or '').strip()} {(current_user.first_name or '').strip()}".strip()
    user_name = full_name or current_user.username

    # Tính toán số lượng chưa đọc mới để cập nhật Header real-time
    unread_count = Review.query.filter_by(is_read=False).count()
    
    # 1. Gửi cho Box Chat (chỉ trong phòng của cuốn sách này)
    emit('receive_message', {
        'message': content,
        'user': user_name,
        'avatar': current_user.avatar,
        'time': datetime.now().strftime('%H:%M'),
        'user_id': current_user.id,
        'msg_id': msg_id,
        'rating': rating
    }, room=room)

    # 2. Gửi cho Header (toàn bộ các trang của tất cả người dùng)
    emit('update_header_reviews', {
        'unread_count': unread_count,
        'new_review': {
            'user': user_name,
            'avatar': current_user.avatar if current_user.avatar else 'https://res.cloudinary.com/dwwfgtxv4/image/upload/v1776585521/AnhDaiDien_nvnfre.png',
            'content': content,
            'rating': rating,
            'id': msg_id,
            'book_id': book_id,
            'time': 'Vừa xong'
        }
    }, broadcast=True)

@socketio.on('delete_message')
def handle_delete_message(data):
    from app.models import Review
    from app import db
    msg_id = data.get('msg_id')
    rev = Review.query.get(msg_id)
    
    if rev and rev.user_id == current_user.id:
        book = rev.book
        db.session.delete(rev)
        db.session.commit()
        
        # Tính toán lại điểm trung bình mới
        new_avg = book.average_rating
        emit('message_deleted', {
            'msg_id': msg_id, 
            'new_avg': new_avg
        }, broadcast=True)

@socketio.on('like_review')
def handle_like_review(data):
    if not current_user.is_authenticated:
        return
    
    from app.models import Review, ReviewLike, Notification
    from app import db
    
    rev_id = data.get('rev_id')
    rev = Review.query.get(rev_id)
    if not rev:
        return

    existing_like = ReviewLike.query.filter_by(user_id=current_user.id, review_id=rev_id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        liked = False
    else:
        new_like = ReviewLike(user_id=current_user.id, review_id=rev_id)
        db.session.add(new_like)
        liked = True
        
        # Tạo thông báo nếu không phải tự mình thích
        if rev.user_id != current_user.id:
            full_name = f"{(current_user.last_name or '').strip()} {(current_user.first_name or '').strip()}".strip()
            user_name = full_name or current_user.username
            
            notif = Notification(
                user_id=rev.user_id,
                title=f"{user_name} đã thích bình luận của bạn",
                content=f"{user_name} đã thích bình luận của bạn về sách '{rev.book.title}'",
                type="LIKE"
            )
            db.session.add(notif)
            db.session.commit()
            
            # Gửi thông báo real-time cho chủ bài viết
            unread_count = Notification.query.filter_by(user_id=rev.user_id, is_read=False).count()
            emit('update_notifications', {
                'unread_count': unread_count,
                'new_notification': {
                    'title': notif.title,
                    'time': 'Vừa xong',
                    'id': notif.id
                }
            }, room=f"user_{rev.user_id}")
        
    db.session.commit()
    
    emit('review_liked', {
        'rev_id': rev_id,
        'like_count': rev.like_count if rev else 0,
        'liked': liked,
        'user_id': current_user.id
    }, broadcast=True)

@socketio.on('reply_review')
def handle_reply_review(data):
    if not current_user.is_authenticated:
        return
        
    from app.models import Review, ReviewReply, Notification
    from app import db
    
    rev_id = data.get('rev_id')
    rev = Review.query.get(rev_id)
    content = data.get('content')
    
    if not content or not rev:
        return
        
    new_reply = ReviewReply(
        content=content,
        user_id=current_user.id,
        review_id=rev_id,
        created_at=datetime.now()
    )
    db.session.add(new_reply)
    
    # Tạo thông báo nếu không phải tự mình phản hồi
    if rev.user_id != current_user.id:
        full_name = f"{(current_user.last_name or '').strip()} {(current_user.first_name or '').strip()}".strip()
        user_name = full_name or current_user.username
        
        notif = Notification(
            user_id=rev.user_id,
            title=f"{user_name} đã phản hồi bình luận của bạn",
            content=f"{user_name} đã phản hồi bình luận của bạn: \"{content[:30]}...\"",
            type="REPLY"
        )
        db.session.add(notif)
        db.session.commit()
        
        # Gửi thông báo real-time
        unread_count = Notification.query.filter_by(user_id=rev.user_id, is_read=False).count()
        emit('update_notifications', {
            'unread_count': unread_count,
            'new_notification': {
                'title': notif.title,
                'time': 'Vừa xong',
                'id': notif.id
            }
        }, room=f"user_{rev.user_id}")

    db.session.commit()
    
    full_name = f"{(current_user.last_name or '').strip()} {(current_user.first_name or '').strip()}".strip()
    user_name = full_name or current_user.username
    
    emit('receive_reply', {
        'rev_id': rev_id,
        'reply_id': new_reply.id,
        'content': content,
        'user': user_name,
        'avatar': current_user.avatar,
        'time': datetime.now().strftime('%H:%M'),
        'user_id': current_user.id
    }, broadcast=True)

