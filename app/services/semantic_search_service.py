import os
import pickle
from app.models import Book

class SemanticSearchService:
    _model = None
    _embeddings_cache = None
    _cache_file = "book_embeddings.pkl"

    @classmethod
    def get_model(cls):
        """Tối ưu: Nạp model một lần duy nhất vào RAM"""
        if cls._model is None:
            # Lazy import để không làm chậm startup nếu không dùng tới
            from sentence_transformers import SentenceTransformer
            print("--- Đang nạp Model AI vào bộ nhớ... ---")
            cls._model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            print("--- Đã nạp xong Model AI! ---")
        return cls._model

    @classmethod
    def compute_embeddings(cls):
        """Tính toán vector cho toàn bộ sách"""
        books = Book.query.all()
        if not books:
            return {}

        model = cls.get_model()
        texts = [f"{b.title} {b.description or ''}" for b in books]
        embeddings = model.encode(texts, show_progress_bar=False)
        
        cache = {b.id: emb for b, emb in zip(books, embeddings)}
        
        with open(cls._cache_file, 'wb') as f:
            pickle.dump(cache, f)
        
        cls._embeddings_cache = cache
        return cache

    @classmethod
    def load_embeddings(cls):
        cls.get_model()
        
        if cls._embeddings_cache is None:
            if os.path.exists(cls._cache_file):
                with open(cls._cache_file, 'rb') as f:
                    cls._embeddings_cache = pickle.load(f)
            else:
                cls._embeddings_cache = {}

        # Kiểm tra xem có sách nào mới chưa có trong cache không
        all_books = Book.query.all()
        new_books = [b for b in all_books if b.id not in cls._embeddings_cache]
        
        if new_books:
            print(f"--- Đang phân tích ý nghĩa cho {len(new_books)} sách mới... ---")
            model = cls.get_model()
            new_texts = [f"{b.title} {b.description or ''}" for b in new_books]
            new_embeddings = model.encode(new_texts, show_progress_bar=False)
            
            for b, emb in zip(new_books, new_embeddings):
                cls._embeddings_cache[b.id] = emb
                
            # Lưu lại vào file để lần sau không phải tính lại
            with open(cls._cache_file, 'wb') as f:
                pickle.dump(cls._embeddings_cache, f)
            print("--- Đã cập nhật xong dữ liệu AI! ---")
            
        return cls._embeddings_cache

    @classmethod
    def search(cls, query, limit=10):
        """Tìm kiếm siêu tốc dùng Numpy"""
        if not query:
            return []

        embeddings_cache = cls.load_embeddings()
        if not embeddings_cache:
            return []

        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        model = cls.get_model()
        query_embedding = model.encode([query], show_progress_bar=False)[0]

        book_ids = list(embeddings_cache.keys())
        book_embeddings = np.array(list(embeddings_cache.values()))

        # Tính toán siêu nhanh bằng ma trận numpy
        similarities = cosine_similarity([query_embedding], book_embeddings)[0]
        
        # Sắp xếp lấy top
        top_indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)[:limit]
        
        results = []
        for i in top_indices:
            score = float(similarities[i])
            # Ngưỡng 0.45 - Cân bằng giữa chính xác và bao quát
            if score > 0.45:
                book = Book.query.get(book_ids[i])
                if book:
                    setattr(book, 'search_score', score)
                    results.append(book)
        
        return results
