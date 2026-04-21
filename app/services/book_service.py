from app.models import Book, Category, db

class BookService:
    @staticmethod
    def get_paginated_books(page=1, per_page=16, order_desc=False):
        query = Book.query
        if order_desc:
            query = query.order_by(Book.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def search_books(keyword='', filters=None, page=1, per_page=16):
        query = Book.query
        
        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.filter(
                db.or_(
                    Book.title.ilike(search_pattern),
                    Book.author.ilike(search_pattern),
                    Book.description.ilike(search_pattern)
                )
            )
            
        if filters:
            if 'category' in filters and filters['category']:
                query = query.filter(Book.category_id == filters['category'])
            if 'language' in filters and filters['language']:
                query = query.filter(Book.language.ilike(filters['language']))
            # Bạn có thể thêm các bộ lọc khác ở đây (ví dụ: năm xuất bản, v.v.)

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_filter_options():
        categories = Category.query.all()
        languages = db.session.query(Book.language).distinct().all()
        # Loại bỏ các giá trị None/rỗng và chuyển thành list chuỗi
        languages = [l[0] for l in languages if l[0]]
        
        return {
            'categories': [{'id': c.id, 'name': c.name} for c in categories],
            'languages': languages
        }
