from sqlalchemy import func
from app.models import Book, Category, BorrowSlip, Favorite, Review, db
from flask_login import current_user

class RecommendationService:
    @staticmethod
    def get_recommendations(user_id, limit=10):
        """
        Gợi ý sách dựa trên:
        1. Thể loại của sách đã mượn
        2. Thể loại của sách trong danh sách yêu thích
        3. Thể loại của sách đã đánh giá cao
        """
        if not user_id:
            return []

        # 1. Tính điểm cho các thể loại dựa trên hành vi
        category_scores = {}

        # Trọng số mượn sách
        borrowed_categories = db.session.query(Book.category_id, func.count(Book.category_id))\
            .join(BorrowSlip, Book.id == BorrowSlip.book_id)\
            .filter(BorrowSlip.user_id == user_id)\
            .group_by(Book.category_id).all()
        for cat_id, count in borrowed_categories:
            category_scores[cat_id] = category_scores.get(cat_id, 0) + (count * 3)

        # Trọng số yêu thích
        fav_categories = db.session.query(Book.category_id, func.count(Book.category_id))\
            .join(Favorite, Book.id == Favorite.book_id)\
            .filter(Favorite.user_id == user_id)\
            .group_by(Book.category_id).all()
        for cat_id, count in fav_categories:
            category_scores[cat_id] = category_scores.get(cat_id, 0) + (count * 2)

        # Trọng số đánh giá cao (Rating >= 4)
        review_categories = db.session.query(Book.category_id, func.count(Book.category_id))\
            .join(Review, Book.id == Review.book_id)\
            .filter(Review.user_id == user_id, Review.rating >= 4)\
            .group_by(Book.category_id).all()
        for cat_id, count in review_categories:
            category_scores[cat_id] = category_scores.get(cat_id, 0) + (count * 2)

        if not category_scores:
            # Nếu người dùng mới chưa có dữ liệu, gợi ý sách có lượt xem cao nhất
            return Book.query.order_by(Book.view_count.desc()).limit(limit).all()

        # 2. Lấy danh sách ID các sách người dùng đã tương tác (để loại trừ)
        interacted_book_ids = db.session.query(BorrowSlip.book_id).filter(BorrowSlip.user_id == user_id).all()
        interacted_book_ids = [r[0] for r in interacted_book_ids]

        # 3. Lấy top thể loại (ví dụ top 3)
        top_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_cat_ids = [c[0] for c in top_categories]

        # 4. Tìm sách trong các thể loại này nhưng người dùng chưa đọc
        recommended_books = Book.query.filter(
            Book.category_id.in_(top_cat_ids),
            ~Book.id.in_(interacted_book_ids)
        ).order_by(Book.view_count.desc()).limit(limit).all()

        # Nếu vẫn ít sách quá, bổ sung thêm sách nổi bật
        if len(recommended_books) < limit:
            extra_books = Book.query.filter(~Book.id.in_(interacted_book_ids))\
                .order_by(Book.view_count.desc())\
                .limit(limit - len(recommended_books)).all()
            recommended_books.extend(extra_books)

        return recommended_books
