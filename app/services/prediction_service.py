from app.models import Book, BorrowSlip, db
from sqlalchemy import func
from datetime import datetime, timedelta

class PredictionService:
    _model = None

    @classmethod
    def prepare_data(cls):
        # 1. Thống kê số lần mượn của mỗi sách 
        three_months_ago = datetime.now() - timedelta(days=90)
        
        borrow_stats = db.session.query(
            BorrowSlip.book_id,
            func.count(BorrowSlip.id).label('borrow_count')
        ).filter(BorrowSlip.borrow_date >= three_months_ago)\
         .group_by(BorrowSlip.book_id).all()
        
        borrow_dict = {b.book_id: b.borrow_count for b in borrow_stats}

        # 2. Lấy thông tin sách
        books = Book.query.all()
        data = []
        for b in books:
            data.append({
                'id': b.id,
                'category_id': b.category_id,
                'price': b.price or 0,
                'view_count': b.view_count or 0,
                'rating': b.average_rating,
                'current_available': b.available_quantity,
                'target_borrow_count': borrow_dict.get(b.id, 0) 
            })
        
        import pandas as pd
        return pd.DataFrame(data)

    @classmethod
    def train_model(cls):
        df = cls.prepare_data()
        if df.empty or len(df) < 5:
            return False

        X = df[['category_id', 'price', 'view_count', 'rating']]
        y = df['target_borrow_count']

        from sklearn.ensemble import RandomForestRegressor
        cls._model = RandomForestRegressor(n_estimators=100, random_state=42)
        cls._model.fit(X, y)
        return True

    @classmethod
    def predict_demand(cls):
        """Dự đoán nhu cầu mượn cho tất cả các sách"""
        if cls._model is None:
            if not cls.train_model():
                return []

        books = Book.query.all()
        if not books:
            return []

        features = []
        for b in books:
            features.append([
                b.category_id,
                b.price or 0,
                b.view_count or 0,
                b.average_rating
            ])
        
        predictions = cls._model.predict(features)
        
        results = []
        for book, pred in zip(books, predictions):
            results.append({
                'book_id': book.id,
                'title': book.title,
                'predicted_demand': float(pred),
                'current_stock': book.available_quantity,
                'risk_level': 'High' if pred > book.available_quantity else 'Normal'
            })
        
        # Sắp xếp theo nhu cầu dự đoán giảm dần
        return sorted(results, key=lambda x: x['predicted_demand'], reverse=True)

    @classmethod
    def get_top_predicted_books(cls, limit=5):
        demands = cls.predict_demand()
        top_ids = [d['book_id'] for d in demands[:limit]]
        return Book.query.filter(Book.id.in_(top_ids)).all()
