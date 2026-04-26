from flask_mail import Message
from app import mail, app
from threading import Thread


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_notification_email(user_email, subject, template_body):
    msg = Message(subject, recipients=[user_email])
    msg.html = template_body

    Thread(target=send_async_email, args=(app, msg)).start()