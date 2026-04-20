from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth

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

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)

    from app import models

    with app.app_context():
        db.create_all()

        # roles = ["admin", "staff", "reader"]
        # for r in roles:
        #     if not Role.query.filter_by(name=r).first():
        #         db.session.add(Role(name=r))
        # db.session.commit()


    return app