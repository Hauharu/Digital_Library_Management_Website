import enum
from app import db
from datetime import datetime
from flask_login import UserMixin


# ================= ENUM =================
class RoleEnum(enum.Enum):
    ADMIN = "ADMIN"
    STAFF = "STAFF"
    READER = "READER"


class GenderEnum(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class RequestStatusEnum(enum.Enum):
    Pending = "Chờ xét duyệt"
    Approved = "Đã duyệt"
    Rejected = "Bị từ chối"
    Completed = "Đã nhận sách"


class BorrowStatusEnum(enum.Enum):
    Borrowing = "Đang mượn"
    Returned = "Đã trả"
    Overdue = "Quá hạn"


class InvoiceStatusEnum(enum.Enum):
    Pending = "Chưa thanh toán"
    Paid = "Đã thanh toán"
    Cancelled = "Đã hủy"
    Overdue = "Quá hạn nộp"


class PaymentStatusEnum(enum.Enum):
    Pending = "Đang xử lý"
    Completed = "Thành công"
    Failed = "Thất bại"
    Refunded = "Đã hoàn tiền"


class PaymentMethodEnum(enum.Enum):
    Cash = "Tiền mặt"
    MoMo = "MoMo"
    ZaloPay = "ZaloPay"
    VNPay = "VNPay"


# ================= BASE =================
class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


# ================= MODEL =================

# ================= USER =================
class User(Base, UserMixin):
    __tablename__ = 'user'

    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)

    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.Enum(GenderEnum), default=GenderEnum.OTHER)
    role = db.Column(db.Enum(RoleEnum), default=RoleEnum.READER, nullable=False)
    avatar = db.Column(db.String(255),
                       default="https://res.cloudinary.com/dwwfgtxv4/image/upload/v1776585521/AnhDaiDien_nvnfre.png")
    is_active = db.Column(db.Boolean, default=True)

    reviews = db.relationship('Review', backref='user', cascade="all, delete-orphan", lazy='selectin')
    borrow_requests = db.relationship('BorrowRequest', backref='reader', cascade="all, delete-orphan", lazy='selectin')
    borrow_slips = db.relationship('BorrowSlip', backref='user', cascade="all, delete-orphan", lazy='selectin')
    notifications = db.relationship('Notification', backref='user', cascade="all, delete-orphan", lazy='selectin')


# ================= CATEGORY =================
class Category(Base):
    __tablename__ = 'category'

    name = db.Column(db.String(100), nullable=False, unique=True)
    books = db.relationship('Book', backref='category', lazy=True)


# ================= BOOK =================
class Book(Base):
    __tablename__ = 'book'
    __table_args__ = (
        db.CheckConstraint('total_quantity >= 0'),
        db.CheckConstraint('available_quantity >= 0'),
        db.CheckConstraint('total_quantity >= available_quantity'),
    )
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(100))
    description = db.Column(db.Text)
    total_quantity = db.Column(db.Integer, default=0)
    available_quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, default=0.0)
    image = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    reviews = db.relationship('Review', backref='book', lazy=True)
    borrow_slips = db.relationship('BorrowSlip', backref='book', lazy=True)


# ================= BORROW REQUEST =================
class BorrowRequest(Base):
    __tablename__ = 'borrow_request'

    request_date = db.Column(db.Date, default=lambda: datetime.now().date())
    status = db.Column(db.Enum(RequestStatusEnum), default=RequestStatusEnum.Pending)
    reject_reason = db.Column(db.String(255))

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)


class BorrowSlip(Base):
    __tablename__ = "borrow_slip"

    borrow_date = db.Column(db.Date, default=lambda: datetime.now().date())
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    status = db.Column(db.Enum(BorrowStatusEnum), default=BorrowStatusEnum.Borrowing)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)

    borrow_request_id = db.Column(db.Integer, db.ForeignKey("borrow_request.id"))
    borrow_request = db.relationship("BorrowRequest", backref="borrow_slip", uselist=False)


# ================= INVOICE =================
class Invoice(Base):
    __tablename__ = 'invoice'

    amount = db.Column(db.Float, nullable=False, default=0.0)
    issue_date = db.Column(db.DateTime, default=datetime.now)
    due_date = db.Column(db.Date)
    status = db.Column(db.Enum(InvoiceStatusEnum), default=InvoiceStatusEnum.Pending)

    # Kết nối với phiếu mượn (để biết phạt cho lần mượn nào)
    borrow_slip_id = db.Column(db.Integer, db.ForeignKey('borrow_slip.id'), unique=True)
    borrow_slip = db.relationship("BorrowSlip", backref="invoices")
    # Quan hệ 1-n với Payment (Một hóa đơn được thanh toán nhiều lần)
    payments = db.relationship('Payment', backref='invoice')


# ================= PAYMENT =================
class Payment(Base):
    __tablename__ = 'payment'

    amount_paid = db.Column(db.Float, nullable=False)
    method = db.Column(db.Enum(PaymentMethodEnum), nullable=False)
    status = db.Column(db.Enum(PaymentStatusEnum), default=PaymentStatusEnum.Pending)
    transaction_id = db.Column(db.String(255), unique=True)
    payment_date = db.Column(db.DateTime, default=datetime.now)
    notes = db.Column(db.Text)

    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)


# ================= REVIEW =================
class Review(Base):
    __tablename__ = 'review'

    __table_args__ = (
        db.UniqueConstraint('user_id', 'book_id', name='unique_review'),
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='valid_rating')
    )
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)


# ================= FAVORITE =================
class Favorite(Base):
    __tablename__ = 'favorite'

    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_favorite'),)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)


# ================= NOTIFICATION =================
class Notification(Base):
    __tablename__ = "notification"
    content = db.Column(db.String(255), nullable=False)
    sent_date = db.Column(db.DateTime, default=datetime.now)
    type = db.Column(db.String(50))
    is_read = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
