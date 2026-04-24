from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import inspect, text

from app import create_app, db,socketio

app = create_app()


with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)

    request_columns = {col['name'] for col in inspector.get_columns('borrow_request')}
    if 'borrow_from_date' not in request_columns:
        db.session.execute(text("ALTER TABLE borrow_request ADD COLUMN borrow_from_date DATE NULL"))
    if 'borrow_to_date' not in request_columns:
        db.session.execute(text("ALTER TABLE borrow_request ADD COLUMN borrow_to_date DATE NULL"))
    if 'quantity' not in request_columns:
        db.session.execute(text("ALTER TABLE borrow_request ADD COLUMN quantity INT NOT NULL DEFAULT 1"))

    slip_columns = {col['name'] for col in inspector.get_columns('borrow_slip')}
    if 'quantity' not in slip_columns:
        db.session.execute(text("ALTER TABLE borrow_slip ADD COLUMN quantity INT NOT NULL DEFAULT 1"))
    if 'return_requested' not in slip_columns:
        db.session.execute(text("ALTER TABLE borrow_slip ADD COLUMN return_requested BOOLEAN NOT NULL DEFAULT FALSE"))

    db.session.commit()



if __name__ == '__main__':
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
