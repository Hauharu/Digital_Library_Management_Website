from flask import Flask
from app import db
from app import models   # import để load bảng

app = Flask(__name__)
app.config.from_object("app.config.Config")

db.init_app(app)

with app.app_context():
    db.create_all()
    print("✅ DB created (lite mode)")