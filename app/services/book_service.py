import math
from app.models import Book, Category, db

class SimplePagination:
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = int(math.ceil(total / float(per_page))) if per_page > 0 else 0

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def prev_num(self):
        return self.page - 1

    @property
    def next_num(self):
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

class BookService:
    @staticmethod
    def search_books(keyword='', filters=None, page=1, per_page=16):
        base_query = Book.query
        if filters:
            if 'category' in filters and filters['category']:
                base_query = base_query.filter(Book.category_id == filters['category'])
            if 'language' in filters and filters['language']:
                base_query = base_query.filter(Book.language.ilike(filters['language']))

        all_books = base_query.all()
        scored_results = []

        if keyword:
            from app.services.semantic_search_service import SemanticSearchService
            semantic_results = SemanticSearchService.search(keyword, limit=50)
            semantic_scores = {b.id: getattr(b, 'search_score', 0) for b in semantic_results}
            
            stop_words = {'và', 'của', 'là', 'trên', 'trong', 'với', 'cho', 'những', 'phần'}
            keywords = [kw for kw in keyword.lower().split() if kw not in stop_words and len(kw) >= 2]

            keyword_lower = keyword.lower()
            for b in all_books:
                # 1. Điểm nền tảng từ AI
                ai_score = semantic_scores.get(b.id, 0)
                
                # 2. Kiểm tra khớp từ khóa SQL
                sql_match = False
                sql_boost = 0
                
                title_lower = b.title.lower()
                desc_lower = (b.description or "").lower()
                author_lower = (b.author or "").lower()
                category_lower = b.category.name.lower()

                # Kiểm tra khớp cả cụm (Ưu tiên cao nhất)
                phrase_match = False
                if (keyword_lower in title_lower or 
                    keyword_lower in category_lower or 
                    keyword_lower in author_lower or
                    keyword_lower in desc_lower):
                    phrase_match = True
                    sql_match = True
                    sql_boost += 0.5  # Thưởng lớn cho khớp cả cụm

                # Kiểm tra từng từ đơn
                for kw in keywords:
                    if kw in title_lower:
                        sql_match = True
                        sql_boost += 0.15
                    if kw in author_lower:
                        sql_match = True
                        sql_boost += 0.1
                    if kw in category_lower:
                        sql_match = True
                        sql_boost += 0.15
                    if kw in desc_lower:
                        sql_match = True
                        sql_boost += 0.1  # Tăng từ 0.05 lên 0.1
                
                # CÔNG THỨC LỌC KÉP:
                if sql_match:
                    # Nếu có khớp cả cụm, điểm tối thiểu cao để chắc chắn hiện
                    if phrase_match:
                        final_score = max(0.65, ai_score + sql_boost)
                        threshold = 0.6
                    else:
                        final_score = max(0.5, ai_score + sql_boost)
                        threshold = 0.55 if ai_score < 0.3 else 0.5
                else:
                    final_score = ai_score
                    threshold = 0.7
                
                final_score = min(1.0, final_score)
                
                if final_score >= threshold:
                    setattr(b, 'search_score', final_score)
                    scored_results.append(b)
            
            scored_results.sort(key=lambda x: getattr(x, 'search_score', 0), reverse=True)
        else:
            scored_results = all_books

        total = len(scored_results)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_items = scored_results[start:end]
        
        return SimplePagination(paginated_items, page, per_page, total)

    @staticmethod
    def get_filter_options():
        categories = Category.query.all()
        languages = db.session.query(Book.language).distinct().all()
        languages = [l[0] for l in languages if l[0]]
        
        return {
            'categories': [{'id': c.id, 'name': c.name} for c in categories],
            'languages': languages
        }
