"""
Mock-based Unit Tests for Book Management Functionality
Test Case 5: Quản lý sách (Admin/Thủ thư)
- Thêm / sửa / xóa sách
- Expected: Dữ liệu lưu đúng DB, Hiển thị cập nhật ngoài giao diện
"""

import unittest
from unittest.mock import patch, MagicMock

# Import service và models để test
from app.services.staff_service import StaffService


class TestBookManagementMock(unittest.TestCase):
    """Test class cho book management service với mock database"""

    def setUp(self):
        """Setup common test data"""
        # Mock book data
        self.book_data = {
            'title': 'Sách Test Mới',
            'author': 'Tác Giả Test',
            'category_id': 1,
            'isbn': '978-3-16-148410-0',
            'price': 150000,
            'total_quantity': 10,
            'description': 'Mô tả sách test'
        }
        
        # Mock updated book data
        self.updated_book_data = {
            'title': 'Sách Test Cập Nhật',
            'author': 'Tác Giả Cập Nhật',
            'category_id': 2,
            'isbn': '978-3-16-148410-1',
            'price': 200000,
            'total_quantity': 15,
            'description': 'Mô tả sách cập nhật'
        }
        
        # Mock book object
        self.mock_book = MagicMock()
        self.mock_book.id = 1
        self.mock_book.title = 'Sách Hiện Có'
        self.mock_book.author = 'Tác Giả Hiện Có'
        self.mock_book.category_id = 1
        self.mock_book.isbn = '978-3-16-148410-0'
        self.mock_book.price = 150000
        self.mock_book.total_quantity = 10
        self.mock_book.available_quantity = 8
        self.mock_book.description = 'Mô tả sách hiện có'
        self.mock_book.image = 'http://example.com/image.jpg'
        
        # Mock image file
        self.mock_image_file = MagicMock()
        self.mock_image_file.filename = 'test_image.jpg'

    # -------- PASS 1: Thêm sách thành công - có hình ảnh ---------
    @patch("app.services.staff_service.db")
    @patch("app.services.staff_service.Book")
    @patch("app.services.staff_service.cloudinary")
    def test_create_book_success_with_image(self, m_cloudinary, m_book, m_db):
        """Test thêm sách thành công với hình ảnh"""
        
        # Mock Cloudinary upload
        mock_upload_result = {
            'secure_url': 'http://cloudinary.com/new_book.jpg'
        }
        m_cloudinary.uploader.upload.return_value = mock_upload_result
        
        # Mock Book constructor
        mock_new_book = MagicMock()
        mock_new_book.id = 123
        m_book.return_value = mock_new_book
        
        # Mock database session
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.rollback = MagicMock()
        m_db.session = mock_session
        
        # Call the service
        result = StaffService.create_book(self.book_data, self.mock_image_file)
        
        # Verify kết quả thành công
        self.assertTrue(result)
        
        # Verify Cloudinary upload được gọi
        m_cloudinary.uploader.upload.assert_called_once_with(
            self.mock_image_file,
            folder="library/books"
        )
        
        # Verify Book được tạo với đúng dữ liệu
        m_book.assert_called_once_with(
            title=self.book_data.get('title'),
            author=self.book_data.get('author'),
            category_id=self.book_data.get('category_id'),
            isbn=self.book_data.get('isbn'),
            price=self.book_data.get('price'),
            total_quantity=self.book_data.get('total_quantity'),
            available_quantity=self.book_data.get('total_quantity'),
            description=self.book_data.get('description'),
            image='http://cloudinary.com/new_book.jpg'
        )
        
        # Verify database operations
        mock_session.add.assert_called_once_with(mock_new_book)
        mock_session.commit.assert_called_once()

    # -------- PASS 2: Thêm sách thành công - không có hình ảnh ---------
    @patch("app.services.staff_service.db")
    @patch("app.services.staff_service.Book")
    def test_create_book_success_no_image(self, m_book, m_db):
        """Test thêm sách thành công không có hình ảnh"""
        
        # Mock Book constructor
        mock_new_book = MagicMock()
        mock_new_book.id = 123
        m_book.return_value = mock_new_book
        
        # Mock database session
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.rollback = MagicMock()
        m_db.session = mock_session
        
        # Mock image file rỗng
        empty_image_file = MagicMock()
        empty_image_file.filename = ''
        
        # Call the service
        result = StaffService.create_book(self.book_data, empty_image_file)
        
        # Verify kết quả thành công
        self.assertTrue(result)
        
        # Verify Book được tạo với image = None
        m_book.assert_called_once_with(
            title=self.book_data.get('title'),
            author=self.book_data.get('author'),
            category_id=self.book_data.get('category_id'),
            isbn=self.book_data.get('isbn'),
            price=self.book_data.get('price'),
            total_quantity=self.book_data.get('total_quantity'),
            available_quantity=self.book_data.get('total_quantity'),
            description=self.book_data.get('description'),
            image=None
        )
        
        # Verify database operations
        mock_session.add.assert_called_once_with(mock_new_book)
        mock_session.commit.assert_called_once()

    # -------- PASS 3: Cập nhật sách thành công ---------
    @patch("app.services.staff_service.db")
    @patch("app.services.staff_service.Book")
    @patch("app.services.staff_service.cloudinary")
    def test_update_book_success(self, m_cloudinary, m_book, m_db):
        """Test cập nhật sách thành công"""
        
        book_id = 1
        
        # Mock Book.query.get
        mock_book_query = MagicMock()
        mock_book_query.get.return_value = self.mock_book
        m_book.query.get = mock_book_query.get
        
        # Mock Cloudinary upload
        mock_upload_result = {
            'url': 'http://cloudinary.com/updated_book.jpg'
        }
        m_cloudinary.uploader.upload.return_value = mock_upload_result
        
        # Mock database session
        mock_session = MagicMock()
        mock_session.commit = MagicMock()
        m_db.session = mock_session
        
        # Call the service
        result = StaffService.update_book(book_id, self.updated_book_data, self.mock_image_file)
        
        # Verify kết quả thành công
        self.assertTrue(result)
        
        # Verify book properties được cập nhật
        self.assertEqual(self.mock_book.title, self.updated_book_data.get('title'))
        self.assertEqual(self.mock_book.price, float(self.updated_book_data.get('price')))
        
        # Verify quantity logic: diff = 15 - 10 = 5
        # available_quantity = 8 + 5 = 13
        expected_available = 8 + 5  # 8 + (15 - 10)
        self.assertEqual(self.mock_book.available_quantity, expected_available)
        self.assertEqual(self.mock_book.total_quantity, 15)
        
        # Verify Cloudinary upload được gọi
        m_cloudinary.uploader.upload.assert_called_once_with(self.mock_image_file)
        
        # Verify database commit
        mock_session.commit.assert_called_once()

    # -------- PASS 4: Cập nhật sách thất bại - không tìm thấy sách ---------
    @patch("app.services.staff_service.Book")
    def test_update_book_not_found(self, m_book):
        """Test cập nhật sách thất bại khi không tìm thấy sách"""
        
        book_id = 999
        
        # Mock Book.query.get trả về None
        mock_book_query = MagicMock()
        mock_book_query.get.return_value = None
        m_book.query.get = mock_book_query.get
        
        # Call the service
        result = StaffService.update_book(book_id, self.updated_book_data, self.mock_image_file)
        
        # Verify kết quả thất bại
        self.assertFalse(result)

    # -------- PASS 5: Cập nhật sách thành công - không có hình ảnh ---------
    @patch("app.services.staff_service.db")
    @patch("app.services.staff_service.Book")
    def test_update_book_success_no_image(self, m_book, m_db):
        """Test cập nhật sách thành công không có hình ảnh"""
        
        book_id = 1
        
        # Mock Book.query.get
        mock_book_query = MagicMock()
        mock_book_query.get.return_value = self.mock_book
        m_book.query.get = mock_book_query.get
        
        # Mock database session
        mock_session = MagicMock()
        mock_session.commit = MagicMock()
        m_db.session = mock_session
        
        # Call the service without image
        result = StaffService.update_book(book_id, self.updated_book_data, None)
        
        # Verify kết quả thành công
        self.assertTrue(result)
        
        # Verify book properties được cập nhật
        self.assertEqual(self.mock_book.title, self.updated_book_data.get('title'))
        self.assertEqual(self.mock_book.price, float(self.updated_book_data.get('price')))
        
        # Verify quantity logic
        expected_available = 8 + 5  # 8 + (15 - 10)
        self.assertEqual(self.mock_book.available_quantity, expected_available)
        self.assertEqual(self.mock_book.total_quantity, 15)
        
        # Verify database commit
        mock_session.commit.assert_called_once()

    # -------- PASS 6: Xóa sách thành công ---------
    @patch("app.services.staff_service.db")
    @patch("app.services.staff_service.Book")
    def test_delete_book_success(self, m_book, m_db):
        """Test xóa sách thành công"""
        
        book_id = 1
        
        # Mock Book.query.get
        mock_book_query = MagicMock()
        mock_book_query.get.return_value = self.mock_book
        m_book.query.get = mock_book_query.get
        
        # Mock borrow_slips (không có sách đang được mượn)
        self.mock_book.borrow_slips = []
        
        # Mock database session
        mock_session = MagicMock()
        mock_session.delete = MagicMock()
        mock_session.commit = MagicMock()
        m_db.session = mock_session
        
        # Call the service
        result = StaffService.delete_book(book_id)
        
        # Verify kết quả thành công
        self.assertTrue(result)
        
        # Verify database operations
        mock_session.delete.assert_called_once_with(self.mock_book)
        mock_session.commit.assert_called_once()

    # -------- PASS 7: Xóa sách thất bại - không tìm thấy sách ---------
    @patch("app.services.staff_service.Book")
    def test_delete_book_not_found(self, m_book):
        """Test xóa sách thất bại khi không tìm thấy sách"""
        
        book_id = 999
        
        # Mock Book.query.get trả về None
        mock_book_query = MagicMock()
        mock_book_query.get.return_value = None
        m_book.query.get = mock_book_query.get
        
        # Call the service
        result = StaffService.delete_book(book_id)
        
        # Verify kết quả thất bại
        self.assertFalse(result)

    # -------- PASS 8: Xóa sách thất bại - sách đang được mượn ---------
    @patch("app.services.staff_service.Book")
    def test_delete_book_borrowed(self, m_book):
        """Test xóa sách thất bại khi sách đang được mượn"""
        
        book_id = 1
        
        # Mock Book.query.get
        mock_book_query = MagicMock()
        mock_book_query.get.return_value = self.mock_book
        m_book.query.get = mock_book_query.get
        
        # Mock borrow_slips (có sách đang được mượn)
        mock_borrowed_slip = MagicMock()
        mock_borrowed_slip.status.name = 'Borrowed'
        self.mock_book.borrow_slips = [mock_borrowed_slip]
        
        # Call the service
        result = StaffService.delete_book(book_id)
        
        # Verify kết quả thất bại với message cụ thể
        self.assertEqual(result, "cannot_delete_borrowed")

    # -------- PASS 9: Thêm sách thất bại - exception ---------
    @patch("app.services.staff_service.db")
    @patch("app.services.staff_service.Book")
    @patch("app.services.staff_service.cloudinary")
    def test_create_book_exception(self, m_cloudinary, m_book, m_db):
        """Test thêm sách thất bại khi có exception"""
        
        # Mock Cloudinary upload
        mock_upload_result = {
            'secure_url': 'http://cloudinary.com/new_book.jpg'
        }
        m_cloudinary.uploader.upload.return_value = mock_upload_result
        
        # Mock Book constructor
        mock_new_book = MagicMock()
        m_book.return_value = mock_new_book
        
        # Mock database session với exception
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.commit.side_effect = Exception("Database error")
        mock_session.rollback = MagicMock()
        m_db.session = mock_session
        
        # Call the service
        result = StaffService.create_book(self.book_data, self.mock_image_file)
        
        # Verify kết quả thất bại
        self.assertFalse(result)
        
        # Verify rollback được gọi
        mock_session.rollback.assert_called_once()

    # -------- PASS 10: Cập nhật sách - giảm số lượng ---------
    @patch("app.services.staff_service.db")
    @patch("app.services.staff_service.Book")
    def test_update_book_decrease_quantity(self, m_book, m_db):
        """Test cập nhật sách khi giảm số lượng tổng"""
        
        book_id = 1
        
        # Mock updated data với số lượng giảm
        decreased_data = self.updated_book_data.copy()
        decreased_data['total_quantity'] = 5  # Giảm từ 10 xuống 5
        
        # Mock Book.query.get
        mock_book_query = MagicMock()
        mock_book_query.get.return_value = self.mock_book
        m_book.query.get = mock_book_query.get
        
        # Mock database session
        mock_session = MagicMock()
        mock_session.commit = MagicMock()
        m_db.session = mock_session
        
        # Call the service
        result = StaffService.update_book(book_id, decreased_data, None)
        
        # Verify kết quả thành công
        self.assertTrue(result)
        
        # Verify quantity logic: diff = 5 - 10 = -5
        # available_quantity = 8 + (-5) = 3
        expected_available = 8 - 5  # 8 + (5 - 10)
        self.assertEqual(self.mock_book.available_quantity, expected_available)
        self.assertEqual(self.mock_book.total_quantity, 5)

    # -------- PASS 11: Lấy tất cả sách ---------
    @patch("app.services.staff_service.db")
    @patch("app.services.staff_service.Book")
    def test_get_all_books(self, m_book, m_db):
        """Test lấy danh sách tất cả sách"""
        
        # Mock books list
        mock_books = [self.mock_book, MagicMock()]
        
        # Mock the entire query chain
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_books
        
        # Mock db.selectinload to avoid SQLAlchemy issues
        m_db.selectinload.return_value = MagicMock()
        
        # Set up the query
        m_book.query = mock_query
        
        # Call the service
        result = StaffService.get_all_books()
        
        # Verify kết quả
        self.assertEqual(len(result), 2)
        self.assertEqual(result, mock_books)
        
        # Verify query được gọi đúng
        mock_query.options.assert_called_once()
        mock_query.order_by.assert_called_once()
        mock_query.all.assert_called_once()

    # -------- PASS 12: Lấy sách theo ID ---------
    @patch("app.services.staff_service.Book")
    def test_get_book_by_id(self, m_book):
        """Test lấy sách theo ID"""
        
        book_id = 1
        
        # Mock Book.query.get_or_404
        mock_book_query = MagicMock()
        mock_book_query.get_or_404.return_value = self.mock_book
        m_book.query.get_or_404 = mock_book_query.get_or_404
        
        # Call the service
        result = StaffService.get_book_by_id(book_id)
        
        # Verify kết quả
        self.assertEqual(result, self.mock_book)
        
        # Verify query được gọi đúng
        mock_book_query.get_or_404.assert_called_once_with(book_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)