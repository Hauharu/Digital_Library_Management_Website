"""
Mock-based Unit Tests for Borrow Approval Functionality
Test Case 4: Duyệt yêu cầu mượn
- Thủ thư xem danh sách yêu cầu
- Chọn duyệt hoặc từ chối
- Expected: Cập nhật trạng thái đúng (Approved / Rejected), Giảm số lượng sách khi duyệt
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import service và models để test
from app.services.staff_service import StaffService
from app.models import RequestStatusEnum, BorrowStatusEnum


class TestBorrowApprovalMock(unittest.TestCase):
    """Test class cho borrow approval service với mock database"""

    def setUp(self):
        """Setup common test data"""
        self.tomorrow = datetime.now().date() + timedelta(days=1)
        self.next_week = datetime.now().date() + timedelta(days=7)
        
        # Mock user
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.first_name = "Nguyễn"
        self.mock_user.last_name = "Văn A"
        self.mock_user.email = "nguyenvana@example.com"
        
        # Mock book with available quantity
        self.mock_book_available = MagicMock()
        self.mock_book_available.id = 1
        self.mock_book_available.title = "Sách Có Sẵn"
        self.mock_book_available.available_quantity = 5
        
        # Mock book with insufficient quantity
        self.mock_book_insufficient = MagicMock()
        self.mock_book_insufficient.id = 2
        self.mock_book_insufficient.title = "Sách Không Đủ Số Lượng"
        self.mock_book_insufficient.available_quantity = 1
        
        # Mock borrow request
        self.mock_borrow_request = MagicMock()
        self.mock_borrow_request.id = 123
        self.mock_borrow_request.user_id = self.mock_user.id
        self.mock_borrow_request.book_id = self.mock_book_available.id
        self.mock_borrow_request.quantity = 2
        self.mock_borrow_request.borrow_to_date = self.next_week
        self.mock_borrow_request.reader = self.mock_user

    # -------- PASS 1: Duyệt yêu cầu thành công - còn đủ sách ---------
    @patch("app.services.staff_service.db")
    @patch("app.services.staff_service.BorrowRequest")
    @patch("app.services.staff_service.Book")
    @patch("app.services.staff_service.BorrowSlip")
    @patch("app.services.staff_service.Notification")
    @patch("app.services.staff_service.socketio")
    @patch("app.services.staff_service.EmailService")
    def test_approve_request_success(self, m_email, m_socketio, m_notification, m_borrow_slip, m_book, m_borrow_request, m_db):
        """Test duyệt yêu cầu mượn sách thành công khi còn đủ sách"""
        
        request_id = 123
        
        # Mock BorrowRequest.query.get_or_404
        mock_request_query = MagicMock()
        mock_request_query.get_or_404.return_value = self.mock_borrow_request
        m_borrow_request.query.get_or_404 = mock_request_query.get_or_404
        
        # Mock Book.query.get
        mock_book_query = MagicMock()
        mock_book_query.get.return_value = self.mock_book_available
        m_book.query.get = mock_book_query.get
        
        # Mock BorrowSlip constructor
        mock_new_slip = MagicMock()
        mock_new_slip.id = 456
        m_borrow_slip.return_value = mock_new_slip
        
        # Mock Notification constructor
        mock_notif = MagicMock()
        mock_notif.id = 789
        m_notification.return_value = mock_notif
        
        # Mock notification count query
        mock_count_query = MagicMock()
        mock_count_query.filter_by.return_value = mock_count_query
        mock_count_query.count.return_value = 1
        
        # Mock database session
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        m_db.session = mock_session
        
        # Mock database queries
        def query_side_effect(model):
            if model == m_notification:
                return mock_count_query
            return mock_count_query
        
        mock_session.query.side_effect = query_side_effect
        
        # Call the service
        result = StaffService.process_approve(request_id)
        
        # Verify kết quả thành công
        self.assertTrue(result[0])  # success flag
        self.assertEqual(result[1], self.mock_user.first_name)  # user name
        
        # Verify BorrowRequest status updated
        self.assertEqual(self.mock_borrow_request.status, RequestStatusEnum.Completed)
        
        # Verify book quantity decreased
        expected_quantity = 5 - 2  # original 5, borrowed 2
        self.assertEqual(self.mock_book_available.available_quantity, expected_quantity)
        
        # Verify BorrowSlip created
        m_borrow_slip.assert_called_once_with(
            borrow_date=datetime.now().date(),
            due_date=self.next_week,
            quantity=2,
            status=BorrowStatusEnum.Borrowing,
            user_id=self.mock_user.id,
            book_id=self.mock_book_available.id,
            borrow_request_id=request_id
        )
        
        # Verify database operations
        mock_session.add.assert_called()  # Add slip and notification
        mock_session.commit.assert_called()  # Commit transaction
        
        # Verify notification created
        m_notification.assert_called_once_with(
            user_id=self.mock_user.id,
            title="Yêu cầu mượn sách đã được duyệt",
            content=f"Cuốn '{self.mock_book_available.title}' đã sẵn sàng để bạn đến lấy.",
            type="SYSTEM"
        )
        
        # Verify SocketIO emission
        m_socketio.emit.assert_called_once()
        
        # Verify Email sent
        m_email.send_approve_notification.assert_called_once()

    # -------- FAIL 1: Duyệt yêu cầu thất bại - không đủ sách ---------
    @patch("app.services.staff_service.BorrowRequest")
    @patch("app.services.staff_service.Book")
    def test_approve_request_insufficient_quantity(self, m_book, m_borrow_request):
        """Test duyệt yêu cầu mượn sách thất bại khi không đủ sách"""
        
        request_id = 123
        
        # Mock borrow request yêu cầu 2 sách
        mock_request = MagicMock()
        mock_request.id = request_id
        mock_request.user_id = self.mock_user.id
        mock_request.book_id = self.mock_book_insufficient.id
        mock_request.quantity = 2  # Yêu cầu 2 sách
        
        mock_request_query = MagicMock()
        mock_request_query.get_or_404.return_value = mock_request
        m_borrow_request.query.get_or_404 = mock_request_query.get_or_404
        
        # Mock book chỉ có 1 sách
        mock_book_query = MagicMock()
        mock_book_query.get.return_value = self.mock_book_insufficient
        m_book.query.get = mock_book_query.get
        
        # Call the service
        result = StaffService.process_approve(request_id)
        
        # Verify kết quả thất bại
        self.assertFalse(result[0])  # failure flag
        self.assertIn("không đủ số lượng", result[1])  # error message
        
        # Verify không tạo BorrowSlip
        # Verify không giảm quantity (vì fail)

    # -------- PASS 2: Từ chối yêu cầu thành công ---------
    @patch("app.services.staff_service.db")
    @patch("app.services.staff_service.BorrowRequest")
    @patch("app.services.staff_service.Notification")
    @patch("app.services.staff_service.socketio")
    @patch("app.services.staff_service.EmailService")
    def test_reject_request_success(self, m_email, m_socketio, m_notification, m_borrow_request, m_db):
        """Test từ chối yêu cầu mượn sách thành công"""
        
        request_id = 123
        reject_reason = "Sách đang được bảo trì"
        
        # Mock borrow request
        mock_request = MagicMock()
        mock_request.id = request_id
        mock_request.user_id = self.mock_user.id
        mock_request.book_id = self.mock_book_available.id
        mock_request.reader = self.mock_user
        
        mock_request_query = MagicMock()
        mock_request_query.get_or_404.return_value = mock_request
        m_borrow_request.query.get_or_404 = mock_request_query.get_or_404
        
        # Mock Notification constructor
        mock_notif = MagicMock()
        mock_notif.id = 789
        m_notification.return_value = mock_notif
        
        # Mock notification count query
        mock_count_query = MagicMock()
        mock_count_query.filter_by.return_value = mock_count_query
        mock_count_query.count.return_value = 1
        
        # Mock database session
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        m_db.session = mock_session
        
        # Mock database queries
        def query_side_effect(model):
            if model == m_notification:
                return mock_count_query
            return mock_count_query
        
        mock_session.query.side_effect = query_side_effect
        
        # Call the service
        result = StaffService.process_reject(request_id, reject_reason)
        
        # Verify kết quả thành công
        self.assertTrue(result)  # success flag
        
        # Verify BorrowRequest status updated
        self.assertEqual(mock_request.status, RequestStatusEnum.Rejected)
        self.assertEqual(mock_request.reject_reason, reject_reason)
        
        # Verify notification created
        m_notification.assert_called_once_with(
            user_id=self.mock_user.id,
            title="Yêu cầu mượn sách bị từ chối",
            content=f"Lý do: {reject_reason}",
            type="SYSTEM"
        )
        
        # Verify database operations
        mock_session.add.assert_called()  # Add notification
        mock_session.commit.assert_called()  # Commit transaction
        
        # Verify SocketIO emission
        m_socketio.emit.assert_called_once()
        
        # Verify Email sent
        m_email.send_reject_notification.assert_called_once()

    # -------- PASS 3: Duyệt yêu cầu - đúng số lượng sách còn lại ---------
    @patch("app.services.staff_service.db")
    @patch("app.services.staff_service.BorrowRequest")
    @patch("app.services.staff_service.Book")
    @patch("app.services.staff_service.BorrowSlip")
    @patch("app.services.staff_service.Notification")
    @patch("app.services.staff_service.socketio")
    @patch("app.services.staff_service.EmailService")
    def test_approve_request_exact_quantity(self, m_email, m_socketio, m_notification, m_borrow_slip, m_book, m_borrow_request, m_db):
        """Test duyệt yêu cầu mượn đúng số lượng sách còn lại"""
        
        request_id = 123
        
        # Mock book có đúng số lượng cần mượn
        book_exact_quantity = MagicMock()
        book_exact_quantity.id = 3
        book_exact_quantity.title = "Sách Đúng Số Lượng"
        book_exact_quantity.available_quantity = 3  # Đúng 3 sách
        
        # Mock borrow request yêu cầu 3 sách
        mock_request = MagicMock()
        mock_request.id = request_id
        mock_request.user_id = self.mock_user.id
        mock_request.book_id = book_exact_quantity.id
        mock_request.quantity = 3
        mock_request.borrow_to_date = self.next_week
        mock_request.reader = self.mock_user
        
        mock_request_query = MagicMock()
        mock_request_query.get_or_404.return_value = mock_request
        m_borrow_request.query.get_or_404 = mock_request_query.get_or_404
        
        mock_book_query = MagicMock()
        mock_book_query.get.return_value = book_exact_quantity
        m_book.query.get = mock_book_query.get
        
        # Mock other components
        mock_new_slip = MagicMock()
        mock_new_slip.id = 456
        m_borrow_slip.return_value = mock_new_slip
        
        mock_notif = MagicMock()
        mock_notif.id = 789
        m_notification.return_value = mock_notif
        
        mock_count_query = MagicMock()
        mock_count_query.filter_by.return_value = mock_count_query
        mock_count_query.count.return_value = 1
        
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        m_db.session = mock_session
        
        mock_session.query.side_effect = lambda model: mock_count_query
        
        # Call the service
        result = StaffService.process_approve(request_id)
        
        # Verify kết quả thành công
        self.assertTrue(result[0])
        
        # Verify book quantity giảm về 0
        self.assertEqual(book_exact_quantity.available_quantity, 0)  # 3 - 3 = 0
        
        # Verify BorrowSlip created
        m_borrow_slip.assert_called_once_with(
            borrow_date=datetime.now().date(),
            due_date=self.next_week,
            quantity=3,
            status=BorrowStatusEnum.Borrowing,
            user_id=self.mock_user.id,
            book_id=book_exact_quantity.id,
            borrow_request_id=request_id
        )

    # -------- PASS 4: Duyệt yêu cầu - quantity = 1 ---------
    @patch("app.services.staff_service.db")
    @patch("app.services.staff_service.BorrowRequest")
    @patch("app.services.staff_service.Book")
    @patch("app.services.staff_service.BorrowSlip")
    @patch("app.services.staff_service.Notification")
    @patch("app.services.staff_service.socketio")
    @patch("app.services.staff_service.EmailService")
    def test_approve_request_single_book(self, m_email, m_socketio, m_notification, m_borrow_slip, m_book, m_borrow_request, m_db):
        """Test duyệt yêu cầu mượn 1 sách"""
        
        request_id = 123
        
        # Mock borrow request chỉ mượn 1 sách
        mock_request = MagicMock()
        mock_request.id = request_id
        mock_request.user_id = self.mock_user.id
        mock_request.book_id = self.mock_book_available.id
        mock_request.quantity = 1
        mock_request.borrow_to_date = self.next_week
        mock_request.reader = self.mock_user
        
        mock_request_query = MagicMock()
        mock_request_query.get_or_404.return_value = mock_request
        m_borrow_request.query.get_or_404 = mock_request_query.get_or_404
        
        mock_book_query = MagicMock()
        mock_book_query.get.return_value = self.mock_book_available
        m_book.query.get = mock_book_query.get
        
        # Mock other components
        mock_new_slip = MagicMock()
        mock_new_slip.id = 456
        m_borrow_slip.return_value = mock_new_slip
        
        mock_notif = MagicMock()
        mock_notif.id = 789
        m_notification.return_value = mock_notif
        
        mock_count_query = MagicMock()
        mock_count_query.filter_by.return_value = mock_count_query
        mock_count_query.count.return_value = 1
        
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        m_db.session = mock_session
        
        mock_session.query.side_effect = lambda model: mock_count_query
        
        # Call the service
        result = StaffService.process_approve(request_id)
        
        # Verify kết quả thành công
        self.assertTrue(result[0])
        
        # Verify book quantity giảm 1
        self.assertEqual(self.mock_book_available.available_quantity, 4)  # 5 - 1 = 4
        
        # Verify BorrowSlip created với quantity = 1
        m_borrow_slip.assert_called_once()
        call_args = m_borrow_slip.call_args[1]
        self.assertEqual(call_args['quantity'], 1)

    # -------- PASS 5: Từ chối yêu cầu - lý do rỗng ---------
    @patch("app.services.staff_service.db")
    @patch("app.services.staff_service.BorrowRequest")
    @patch("app.services.staff_service.Notification")
    @patch("app.services.staff_service.socketio")
    @patch("app.services.staff_service.EmailService")
    def test_reject_request_empty_reason(self, m_email, m_socketio, m_notification, m_borrow_request, m_db):
        """Test từ chối yêu cầu với lý do rỗng"""
        
        request_id = 123
        reject_reason = ""  # Lý do rỗng
        
        # Mock borrow request
        mock_request = MagicMock()
        mock_request.id = request_id
        mock_request.user_id = self.mock_user.id
        mock_request.book_id = self.mock_book_available.id
        mock_request.reader = self.mock_user
        
        mock_request_query = MagicMock()
        mock_request_query.get_or_404.return_value = mock_request
        m_borrow_request.query.get_or_404 = mock_request_query.get_or_404
        
        # Mock other components
        mock_notif = MagicMock()
        mock_notif.id = 789
        m_notification.return_value = mock_notif
        
        mock_count_query = MagicMock()
        mock_count_query.filter_by.return_value = mock_count_query
        mock_count_query.count.return_value = 1
        
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        m_db.session = mock_session
        
        mock_session.query.side_effect = lambda model: mock_count_query
        
        # Call the service
        result = StaffService.process_reject(request_id, reject_reason)
        
        # Verify kết quả thành công (vẫn cho phép từ chối với lý do rỗng)
        self.assertTrue(result)
        
        # Verify BorrowRequest status updated
        self.assertEqual(mock_request.status, RequestStatusEnum.Rejected)
        self.assertEqual(mock_request.reject_reason, reject_reason)
        
        # Verify notification created với lý do rỗng
        m_notification.assert_called_once_with(
            user_id=self.mock_user.id,
            title="Yêu cầu mượn sách bị từ chối",
            content=f"Lý do: {reject_reason}",
            type="SYSTEM"
        )

    # -------- PASS 6: Edge case - approve với quantity lớn ---------
    @patch("app.services.staff_service.db")
    @patch("app.services.staff_service.BorrowRequest")
    @patch("app.services.staff_service.Book")
    @patch("app.services.staff_service.BorrowSlip")
    @patch("app.services.staff_service.Notification")
    @patch("app.services.staff_service.socketio")
    @patch("app.services.staff_service.EmailService")
    def test_approve_request_large_quantity(self, m_email, m_socketio, m_notification, m_borrow_slip, m_book, m_borrow_request, m_db):
        """Test duyệt yêu cầu mượn số lượng lớn"""
        
        request_id = 123
        
        # Mock book có nhiều sách
        book_large_quantity = MagicMock()
        book_large_quantity.id = 4
        book_large_quantity.title = "Sách Nhiều Cuốn"
        book_large_quantity.available_quantity = 100
        
        # Mock borrow request yêu cầu nhiều sách
        mock_request = MagicMock()
        mock_request.id = request_id
        mock_request.user_id = self.mock_user.id
        mock_request.book_id = book_large_quantity.id
        mock_request.quantity = 50
        mock_request.borrow_to_date = self.next_week
        mock_request.reader = self.mock_user
        
        mock_request_query = MagicMock()
        mock_request_query.get_or_404.return_value = mock_request
        m_borrow_request.query.get_or_404 = mock_request_query.get_or_404
        
        mock_book_query = MagicMock()
        mock_book_query.get.return_value = book_large_quantity
        m_book.query.get = mock_book_query.get
        
        # Mock other components
        mock_new_slip = MagicMock()
        mock_new_slip.id = 456
        m_borrow_slip.return_value = mock_new_slip
        
        mock_notif = MagicMock()
        mock_notif.id = 789
        m_notification.return_value = mock_notif
        
        mock_count_query = MagicMock()
        mock_count_query.filter_by.return_value = mock_count_query
        mock_count_query.count.return_value = 1
        
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        m_db.session = mock_session
        
        mock_session.query.side_effect = lambda model: mock_count_query
        
        # Call the service
        result = StaffService.process_approve(request_id)
        
        # Verify kết quả thành công
        self.assertTrue(result[0])
        
        # Verify book quantity giảm đúng
        self.assertEqual(book_large_quantity.available_quantity, 50)  # 100 - 50 = 50
        
        # Verify BorrowSlip created với quantity lớn
        m_borrow_slip.assert_called_once()
        call_args = m_borrow_slip.call_args[1]
        self.assertEqual(call_args['quantity'], 50)


if __name__ == "__main__":
    unittest.main(verbosity=2)