"""
Data Access Object for Book operations
"""

from app.models import Book, Category, db
from sqlalchemy import func


def search_books(
    title=None,
    author=None,
    category_id=None,
    category_name=None,
    language=None,
    min_price=None,
    max_price=None,
    available_only=False,
    limit=None,
    page=1,
    per_page=16
):
    """
    Tìm kiếm sách với nhiều bộ lọc khác nhau
    
    Args:
        title (str): Lọc theo tên sách
        author (str): Lọc theo tên tác giả
        category_id (int): Lọc theo ID danh mục
        category_name (str): Lọc theo tên danh mục
        language (str): Lọc theo ngôn ngữ
        min_price (float): Lọc theo giá tối thiểu
        max_price (float): Lọc theo giá tối đa
        available_only (bool): Chỉ hiển thị sách có available_quantity > 0
        limit (int): Giới hạn số lượng kết quả
        page (int): Số trang cho phân trang
        per_page (int): Số mục trên mỗi trang
    
    Returns:
        Đối tượng phân trang chứa danh sách sách
    """
    query = db.session.query(Book).join(Category)
    
    # Áp dụng các bộ lọc
    if title:
        query = query.filter(Book.title.ilike(f'%{title}%'))
    
    if author:
        query = query.filter(Book.author.ilike(f'%{author}%'))
    
    if category_id:
        query = query.filter(Book.category_id == category_id)
    
    if category_name:
        query = query.filter(Category.name.ilike(f'%{category_name}%'))
    
    if language:
        query = query.filter(Book.language.ilike(f'%{language}%'))
    
    if min_price is not None:
        query = query.filter(Book.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Book.price <= max_price)
    
    if available_only:
        query = query.filter(Book.available_quantity > 0)
    
    # Order by title
    query = query.order_by(Book.title)
    
    # Apply limit if specified
    if limit:
        query = query.limit(limit)
    
    # Paginate
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return pagination


def get_book_by_id(book_id):
    """
    Lấy sách theo ID
    
    Args:
        book_id (int): ID của sách
    
    Returns:
        Đối tượng Book hoặc None
    """
    return db.session.query(Book).join(Category).filter(Book.id == book_id).first()


def get_books_by_category(category_id, page=1, per_page=16):
    """
    Lấy sách theo danh mục
    
    Args:
        category_id (int): ID của danh mục
        page (int): Số trang
        per_page (int): Số mục trên mỗi trang
    
    Returns:
        Đối tượng phân trang chứa danh sách sách
    """
    query = db.session.query(Book).filter(Book.category_id == category_id)
    
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )


def get_featured_books(limit=10):
    """
    Lấy sách nổi bật (xem nhiều nhất)
    
    Args:
        limit (int): Số lượng sách cần trả về
    
    Returns:
        Danh sách các đối tượng Book
    """
    return db.session.query(Book).join(Category).order_by(Book.view_count.desc()).limit(limit).all()


def get_random_books(limit=10):
    """
    Lấy sách ngẫu nhiên
    
    Args:
        limit (int): Số lượng sách cần trả về
    
    Returns:
        Danh sách các đối tượng Book
    """
    return db.session.query(Book).join(Category).order_by(func.random()).limit(limit).all()


def search_books_advanced(filters=None, page=1, per_page=16):
    """
    Tìm kiếm nâng cao với nhiều bộ lọc
    
    Args:
        filters (dict): Dictionary chứa các bộ lọc
        page (int): Số trang
        per_page (int): Số mục trên mỗi trang
    
    Returns:
        Đối tượng phân trang chứa danh sách sách
    """
    if not filters:
        filters = {}
    
    return search_books(
        title=filters.get('title'),
        author=filters.get('author'),
        category_id=filters.get('category'),
        language=filters.get('language'),
        min_price=filters.get('min_price'),
        max_price=filters.get('max_price'),
        available_only=filters.get('available_only', False),
        page=page,
        per_page=per_page
    )
