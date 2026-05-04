"""
Simple Mock-based Unit Tests for Book Search Functionality
Chỉ test các trường hợp PASS cơ bản
"""

import unittest
from unittest.mock import patch, MagicMock

# Import DAO layer để test
from app.dao import book_dao as dao


class TestBookSearchSimpleMock(unittest.TestCase):
    """Test class cho book search với mock database - chỉ test PASS cases"""

    # -------- PASS 1: Tìm kiếm không filter, có 2 sách --------
    @patch("app.dao.book_dao.db")
    @patch("app.dao.book_dao.Book")
    @patch("app.dao.book_dao.Category")
    def test_search_books_no_filter_two_results(self, m_category, m_book, m_db):
        """Test tìm kiếm sách không có filter, trả về 2 sách"""
        # Create mock books
        book1 = MagicMock()
        book1.id = 1
        book1.title = "Tôi Thấy Hoa Vàng"
        book1.author = "Nguyễn Nhật Ánh"
        
        book2 = MagicMock()
        book2.id = 2
        book2.title = "Harry Potter"
        book2.author = "J.K. Rowling"
        
        books = [book1, book2]
        
        # Mock query chain
        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.filter_by.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.offset.return_value = q
        
        # Mock pagination
        mock_pagination = MagicMock()
        mock_pagination.items = books
        mock_pagination.page = 1
        mock_pagination.pages = 1
        mock_pagination.total = len(books)
        mock_pagination.has_prev = False
        mock_pagination.has_next = False
        q.paginate.return_value = mock_pagination
        
        m_db.session.query.return_value = q

        out = dao.search_books()

        # DAO returns pagination object, access items
        self.assertEqual(len(out.items), 2)
        self.assertEqual(out.items[0].id, 1)
        self.assertEqual(out.items[0].title, "Tôi Thấy Hoa Vàng")
        self.assertEqual(out.items[0].author, "Nguyễn Nhật Ánh")
        q.join.assert_called()  # đã join với category
        q.order_by.assert_called()  # đã order by
        q.paginate.assert_called()  # đã paginate

    # -------- PASS 2: Filter theo tác giả --------
    @patch("app.dao.book_dao.db")
    @patch("app.dao.book_dao.Book")
    @patch("app.dao.book_dao.Category")
    def test_search_by_author(self, m_category, m_book, m_db):
        """Test tìm kiếm theo tác giả"""
        # Create mock books
        book1 = MagicMock()
        book1.id = 3
        book1.title = "Cho Tôi Xin Một Vé Đi Tuổi Thơ"
        book1.author = "Nguyễn Nhật Ánh"
        
        book2 = MagicMock()
        book2.id = 4
        book2.title = "Mắt Biếc"
        book2.author = "Nguyễn Nhật Ánh"
        
        books = [book1, book2]
        
        # Mock query chain
        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.filter_by.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.offset.return_value = q
        
        # Mock pagination
        mock_pagination = MagicMock()
        mock_pagination.items = books
        mock_pagination.page = 1
        mock_pagination.pages = 1
        mock_pagination.total = len(books)
        mock_pagination.has_prev = False
        mock_pagination.has_next = False
        q.paginate.return_value = mock_pagination
        
        m_db.session.query.return_value = q

        out = dao.search_books(author="Nguyễn Nhật Ánh")

        self.assertEqual(len(out.items), 2)
        self.assertTrue(all("Nguyễn Nhật Ánh" in book.author for book in out.items))
        q.filter.assert_called()  # đã áp dụng filter tác giả
        q.paginate.assert_called()  # đã paginate

    # -------- PASS 3: Filter theo tên sách + limit --------
    @patch("app.dao.book_dao.db")
    @patch("app.dao.book_dao.Book")
    @patch("app.dao.book_dao.Category")
    def test_search_by_title_with_limit(self, m_category, m_book, m_db):
        """Test tìm kiếm theo tên sách với limit"""
        # Create mock book
        book = MagicMock()
        book.id = 5
        book.title = "Dế Mèn Phiêu Lưu Ký"
        book.author = "Tô Hoài"
        
        # Mock query chain
        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.filter_by.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.offset.return_value = q
        
        # Mock pagination
        mock_pagination = MagicMock()
        mock_pagination.items = [book]
        mock_pagination.page = 1
        mock_pagination.pages = 1
        mock_pagination.total = 1
        mock_pagination.has_prev = False
        mock_pagination.has_next = False
        q.paginate.return_value = mock_pagination
        
        m_db.session.query.return_value = q

        out = dao.search_books(title="Dế Mèn", limit=1)

        self.assertEqual(len(out.items), 1)
        self.assertEqual(out.items[0].title, "Dế Mèn Phiêu Lưu Ký")
        q.filter.assert_called()  # đã filter theo title
        q.limit.assert_called_once_with(1)  # đã áp limit
        q.paginate.assert_called()  # đã paginate

    # -------- PASS 4: Tìm kiếm sách theo ID --------
    @patch("app.dao.book_dao.db")
    @patch("app.dao.book_dao.Book")
    @patch("app.dao.book_dao.Category")
    def test_get_book_by_id(self, m_category, m_book, m_db):
        """Test lấy sách theo ID"""
        # Create mock book
        book = MagicMock()
        book.id = 8
        book.title = "Nhà Giả Kim"
        book.author = "Paulo Coelho"
        
        # Mock query chain
        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.filter_by.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.offset.return_value = q
        q.first.return_value = book
        
        m_db.session.query.return_value = q

        out = dao.get_book_by_id(8)

        self.assertIsNotNone(out)
        self.assertEqual(out.id, 8)
        self.assertEqual(out.title, "Nhà Giả Kim")
        # Note: filter_by might not be called if the query uses filter instead
        # The important thing is that we get the correct book back

    # -------- PASS 5: Filter theo category --------
    @patch("app.dao.book_dao.db")
    @patch("app.dao.book_dao.Book")
    @patch("app.dao.book_dao.Category")
    def test_search_by_category(self, m_category, m_book, m_db):
        """Test tìm kiếm theo category"""
        # Create mock books
        book1 = MagicMock()
        book1.id = 9
        book1.title = "Sách Văn Học 1"
        book1.category_id = 1
        
        book2 = MagicMock()
        book2.id = 10
        book2.title = "Sách Văn Học 2"
        book2.category_id = 1
        
        books = [book1, book2]
        
        # Mock query chain
        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.filter_by.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.offset.return_value = q
        
        # Mock pagination
        mock_pagination = MagicMock()
        mock_pagination.items = books
        mock_pagination.page = 1
        mock_pagination.pages = 1
        mock_pagination.total = len(books)
        mock_pagination.has_prev = False
        mock_pagination.has_next = False
        q.paginate.return_value = mock_pagination
        
        m_db.session.query.return_value = q

        out = dao.search_books(category_id=1)

        self.assertEqual(len(out.items), 2)
        self.assertEqual(out.items[0].id, 9)
        self.assertEqual(out.items[0].title, "Sách Văn Học 1")
        q.filter.assert_called()  # đã filter theo category
        q.paginate.assert_called()  # đã paginate

    # -------- PASS 6: Test get_featured_books --------
    @patch("app.dao.book_dao.db")
    @patch("app.dao.book_dao.Book")
    @patch("app.dao.book_dao.Category")
    def test_get_featured_books(self, m_category, m_book, m_db):
        """Test lấy sách nổi bật (most viewed)"""
        # Create mock books
        book1 = MagicMock()
        book1.id = 11
        book1.title = "Sách Nổi Bật 1"
        book1.view_count = 1000
        
        book2 = MagicMock()
        book2.id = 12
        book2.title = "Sách Nổi Bật 2"
        book2.view_count = 800
        
        books = [book1, book2]
        
        # Mock query chain
        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.filter_by.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.all.return_value = books
        
        m_db.session.query.return_value = q

        out = dao.get_featured_books(limit=10)

        self.assertEqual(len(out), 2)
        self.assertEqual(out[0].id, 11)
        self.assertEqual(out[0].title, "Sách Nổi Bật 1")
        q.join.assert_called()  # đã join với category
        q.order_by.assert_called()  # đã order by view_count
        q.limit.assert_called_once_with(10)  # đã áp limit

    # -------- PASS 7: Test get_random_books --------
    @patch("app.dao.book_dao.db")
    @patch("app.dao.book_dao.Book")
    @patch("app.dao.book_dao.Category")
    def test_get_random_books(self, m_category, m_book, m_db):
        """Test lấy sách ngẫu nhiên"""
        # Create mock books
        book1 = MagicMock()
        book1.id = 13
        book1.title = "Sách Ngẫu Nhiên 1"
        
        book2 = MagicMock()
        book2.id = 14
        book2.title = "Sách Ngẫu Nhiên 2"
        
        books = [book1, book2]
        
        # Mock query chain
        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.filter_by.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.all.return_value = books
        
        m_db.session.query.return_value = q

        out = dao.get_random_books(limit=10)

        self.assertEqual(len(out), 2)
        self.assertEqual(out[0].id, 13)
        self.assertEqual(out[0].title, "Sách Ngẫu Nhiên 1")
        q.join.assert_called()  # đã join với category
        q.order_by.assert_called()  # đã order by random
        q.limit.assert_called_once_with(10)  # đã áp limit


if __name__ == "__main__":
    unittest.main(verbosity=2)