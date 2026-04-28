# 📚 Digital Library Management Website

Hệ thống Quản lý Thư viện Số hiện đại được xây dựng với Python Flask, tích hợp các tính năng AI nâng cao.

## 🌟 Tính năng nổi bật
- **Tìm kiếm kết hợp (Hybrid Search)**: Tìm kiếm chính xác theo từ khóa và tìm kiếm theo ngữ nghĩa (Semantic Search) dựa trên mô hình AI.
- **Dự báo nhu cầu**: Sử dụng Machine Learning (RandomForest) để dự báo nhu cầu mượn sách.
- **Tối ưu hóa hiệu suất**: Nạp mô hình AI bất đồng bộ/thông minh để thời gian khởi động ứng dụng luôn ở mức < 0.1s.
- **Quản lý mượn/trả**: Đầy đủ quy trình mượn, trả sách và quản lý kho.

---

## 🏛 System Architecture
<img width="694" height="627" alt="Image" src="https://github.com/user-attachments/assets/603e9f7f-a88d-4044-8b1b-e7218be9bf1a" />

---

## 📖 Hướng dẫn cài đặt & chạy project

### 🔧 Yêu cầu môi trường
Để chạy được project, máy tính của bạn cần cài đặt sẵn:
- **Python 3.10+** (Khuyên dùng Python 3.11)
- **MySQL 8.0+**
- PyCharm, VSCode (hoặc IDE khác hỗ trợ Python)

---

### 🚀 Các bước cài đặt chi tiết

#### 1. Clone project về máy
Mở Terminal / Command Prompt và chạy lệnh sau:
```bash
git clone https://github.com/Hauharu/Digital_Library_Management_Website.git
cd Digital_Library_Management_Website
```

#### 2. Thiết lập môi trường ảo (Virtual Environment)
Môi trường ảo giúp các thư viện của dự án không bị xung đột với hệ thống.
```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường ảo
# - Trên Windows:
.venv\Scripts\activate
# - Trên macOS/Linux:
source .venv/bin/activate

# Cài đặt toàn bộ thư viện cần thiết (bao gồm cả các gói AI)
pip install -r requirements.txt
```

#### 3. Tạo cơ sở dữ liệu MySQL
- Mở MySQL Workbench hoặc công cụ quản trị MySQL của bạn.
- Tạo một database mới với tên `library_db`:
```sql
CREATE DATABASE library_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 4. Cấu hình thông tin dự án (`app/config.py` hoặc `.env`)
Bạn có 2 cách để cấu hình các thông số kết nối (Database, Email, Cloudinary...):

**Cách 1: Sửa trực tiếp trong code (Dành cho môi trường dev)**
- Mở file `app/config.py` và thay đổi trực tiếp các giá trị mặc định trong hàm `os.getenv()` thành thông tin của bạn.

**Cách 2: Sử dụng file `.env` (Khuyên dùng, bảo mật cao)**
1. Tạo một file tên là `.env` ở thư mục gốc của project (ngang hàng với `index.py`).
2. Copy và dán đoạn code sau vào file `.env`, đồng thời **thay thế các giá trị bằng thông tin thực tế** của bạn:

```env
# ==========================================
# CẤU HÌNH DATABASE (MySQL)
# ==========================================
DB_USER=root
DB_PASSWORD=your_mysql_password_here
DB_HOST=localhost
DB_PORT=3306
DB_NAME=library_db

# ==========================================
# BẢO MẬT ỨNG DỤNG
# ==========================================
FLASK_ENV=development
SECRET_KEY=your_secret_key_here

# ==========================================
# CLOUDINARY (Lưu trữ ảnh)
# ==========================================
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# ==========================================
# EMAIL SMTP (Gửi mail)
# ==========================================
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com

# ==========================================
# ĐĂNG NHẬP GOOGLE OAUTH
# ==========================================
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# ==========================================
# GEMINI AI (Tuỳ chọn nếu có)
# ==========================================
GEMINI_API_KEY=your_gemini_api_key
```

*Lưu ý: Không bao giờ commit file `.env` lên GitHub để tránh lộ thông tin bảo mật.*

#### 5. Khởi tạo cơ sở dữ liệu và dữ liệu mẫu
Ứng dụng được thiết kế tự động tạo các bảng khi chạy lần đầu tiên.
- Bạn có thể nạp thêm dữ liệu mẫu vào database `library_db` bằng cách chạy script trong file `data_library_db.txt` trực tiếp trên MySQL.

#### 6. Chạy ứng dụng
Khởi động server bằng file `index.py`:
```bash
python index.py
```
*Lưu ý: Trong lần khởi chạy đầu tiên, hệ thống sẽ mất một vài giây để tự động tải và khởi tạo "Bộ não AI" (Model SentenceTransformers) vào RAM. Các lần tải trang sau sẽ nhanh chóng.*

#### 7. Truy cập website
Mở trình duyệt web của bạn và truy cập vào địa chỉ:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 👥 Tài khoản thử nghiệm
- **Nhân viên / Admin**: Vui lòng tạo tài khoản và set role trong Database.
- **Khách hàng**: Có thể tự đăng ký trực tiếp trên giao diện trang web.
