from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.decorators import role_required
from app.models import RoleEnum, Book, Category, db
import cloudinary.uploader

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/add-book', methods=['GET', 'POST'])
@login_required
@role_required(RoleEnum.ADMIN)
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        isbn = request.form.get('isbn')
        author = request.form.get('author')
        category_id = request.form.get('category_id')
        price = request.form.get('price', 0)
        language = request.form.get('language')
        total_quantity = request.form.get('total_quantity', 0)
        publication_info = request.form.get('publication_info')
        description = request.form.get('description')
        
        image_file = request.files.get('image')
        image_url = None
        
        if image_file:
            try:
                # Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(image_file)
                image_url = upload_result.get('secure_url')
            except Exception as e:
                flash(f"Lỗi khi tải ảnh lên Cloudinary: {str(e)}", "warning")

        new_book = Book(
            title=title,
            isbn=isbn,
            author=author,
            category_id=category_id,
            price=float(price) if price else 0.0,
            language=language,
            total_quantity=int(total_quantity) if total_quantity else 0,
            available_quantity=int(total_quantity) if total_quantity else 0,
            publication_info=publication_info,
            description=description,
            image=image_url
        )
        
        try:
            db.session.add(new_book)
            db.session.commit()
            flash("Thêm sách mới thành công!", "success")
            return redirect(url_for('main.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi khi thêm sách vào cơ sở dữ liệu: {str(e)}", "danger")

    categories = Category.query.all()
    return render_template('admin/add_book.html', categories=categories)

@admin_bp.route('/books')
@login_required
@role_required(RoleEnum.ADMIN)
def manage_books():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = Book.query.order_by(Book.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items
    return render_template('admin/manage_books.html', books=books, pagination=pagination)
