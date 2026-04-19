from flask import Blueprint, render_template
from app.models import Book

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    featured_books = Book.query.limit(8).all()
    return render_template('index.html', featured_books=featured_books)
