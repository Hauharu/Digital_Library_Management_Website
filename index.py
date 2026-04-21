from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import inspect, text

from app import create_app, db
from app.models import Book
from app.services.borrow_service import BorrowService

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


@app.route('/borrow/<int:book_id>', methods=['GET', 'POST'])
@login_required
def borrow_book(book_id):
    book = Book.query.get_or_404(book_id)
    quantity_available = book.available_quantity or 0

    if request.method == 'POST':
        start_date_str = request.form.get('start_date', '').strip()
        end_date_str = request.form.get('end_date', '').strip()
        quantity_str = request.form.get('quantity', '1').strip()

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Ngày mượn hoặc ngày trả không hợp lệ.', 'danger')
            return redirect(url_for('borrow_book', book_id=book_id))

        try:
            quantity = int(quantity_str)
        except ValueError:
            flash('Số lượng mượn phải là số nguyên.', 'danger')
            return redirect(url_for('borrow_book', book_id=book_id))

        result = BorrowService.create_borrow_request(
            user=current_user,
            book=book,
            start_date=start_date,
            end_date=end_date,
            quantity=quantity
        )

        flash(result['message'], result['category'])
        if result['ok']:
            return redirect(url_for('main.book_detail', book_id=book_id, **{'from': 'featured'}))

        return redirect(url_for('borrow_book', book_id=book_id))

    return render_template(
        'book/borrow_form.html',
        user=current_user,
        book=book,
        quantity_available=quantity_available,
        today=datetime.now().date().isoformat()
    )


if __name__ == '__main__':
    app.run(debug=True)
