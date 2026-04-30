from app import create_app, db
from app.models import Book

app = create_app()
with app.app_context():
    book = Book.query.get(2)
    if book:
        print(f"Book ID: {book.id}")
        print(f"Title: {book.title}")
        print(f"Total Quantity: {book.total_quantity}")
        print(f"Available Quantity: {book.available_quantity}")
    else:
        print("Book not found")
