// Biến toàn cục lưu trữ danh sách ID sách đang chọn
let selectedBooks = [];

/**
 * 1. KIỂM TRA ĐỘC GIẢ
 */
async function checkReader() {
    const phoneInput = document.getElementById('phone-input');
    const phone = phoneInput.value.trim();

    if (!phone) {
        alert("Vui lòng nhập số điện thoại độc giả!");
        return;
    }

    try {
        const response = await fetch(`/staff/api/check-reader?phone=${phone}`);
        const data = await response.json();

        const quickRegForm = document.getElementById('quick-reg-form');
        const readerInfo = document.getElementById('reader-info');

        if (data.exists) {
            // Hiển thị thông tin độc giả tìm thấy
            showReaderInfo(data.id, data.name, phone);
        } else {
            // Không tìm thấy, hiện form đăng ký nhanh
            readerInfo.classList.add('d-none');
            quickRegForm.classList.remove('d-none');
            document.getElementById('new-name').focus();
        }
    } catch (error) {
        console.error("Lỗi hệ thống:", error);
        alert("Không thể kết nối đến máy chủ!");
    }
}

/**
 * 2. ĐĂNG KÝ NHANH ĐỘC GIẢ
 */
async function quickRegister() {
    const phone = document.getElementById('phone-input').value;
    const name = document.getElementById('new-name').value.trim();

    if (!name) {
        alert("Vui lòng nhập họ tên khách!");
        return;
    }

    try {
        const response = await fetch('/staff/api/quick-register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone: phone, full_name: name })
        });

        const data = await response.json();

        if (data.success) {
            alert("Đã tạo tài khoản thành công!");
            // Gọi hàm hiển thị thông tin với đầy đủ các trường
            showReaderInfo(data.id, data.name, data.phone, data.email);
        } else {
            alert("Không thể tạo: " + data.message);
        }
    } catch (error) {
        console.error("Lỗi:", error);
        alert("Lỗi kết nối server!");
    }
}
// Hàm bổ trợ hiển thị vùng thông tin người dùng
function showReaderInfo(id, name, phone, email) {
    document.getElementById('selected-user-id').value = id;
    document.getElementById('reader-name-display').innerText = name;
    // Hiển thị cả 2 để xác nhận đúng người
    document.getElementById('reader-phone-display').innerText = `${phone} | ${email}`;
    document.getElementById('reader-avatar').innerText = name.charAt(0).toUpperCase();

    document.getElementById('reader-info').classList.remove('d-none');
    document.getElementById('quick-reg-form').classList.add('d-none');
}
/**
 * 3. QUẢN LÝ DANH SÁCH SÁCH MƯỢN
 */
function addBookToQueue() {
    const select = document.getElementById('book-select');
    const bookId = select.value;
    const option = select.options[select.selectedIndex];

    if (!bookId) {
        alert("Vui lòng chọn một cuốn sách!");
        return;
    }

    // Kiểm tra trùng lặp
    if (selectedBooks.includes(bookId)) {
        alert("Sách này đã có trong danh sách mượn!");
        return;
    }

    const bookName = option.text;
    const bookPrice = option.getAttribute('data-price');

    // Cập nhật mảng lưu trữ
    selectedBooks.push(bookId);

    // Thêm dòng vào bảng
    const tbody = document.getElementById('borrow-list');
    const row = document.createElement('tr');
    row.id = `book-row-${bookId}`;
    row.innerHTML = `
        <td class="ps-3 fw-medium">${bookName}</td>
        <td>${new Intl.NumberFormat('vi-VN').format(bookPrice)} đ</td>
        <td class="text-end pe-3">
            <button class="btn btn-sm btn-outline-danger border-0" onclick="removeBook('${bookId}')">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    tbody.appendChild(row);

    updateUI();
}

function removeBook(bookId) {
    // Xóa khỏi mảng
    selectedBooks = selectedBooks.filter(id => id !== bookId);

    // Xóa khỏi giao diện
    const row = document.getElementById(`book-row-${bookId}`);
    if (row) row.remove();

    updateUI();
}

// Cập nhật các thành phần nhỏ trên giao diện (số lượng, thông báo trống)
function updateUI() {
    const emptyMsg = document.getElementById('empty-list-msg');
    const countDisplay = document.getElementById('book-count');

    countDisplay.innerText = selectedBooks.length;

    if (selectedBooks.length > 0) {
        emptyMsg.classList.add('d-none');
    } else {
        emptyMsg.classList.remove('d-none');
    }
}

/**
 * 4. GỬI PHIẾU MƯỢN LÊN SERVER
 */
async function submitBorrowSlip() {
    const userId = document.getElementById('selected-user-id').value;

    if (!userId) {
        alert("Vui lòng xác định độc giả trước!");
        return;
    }

    if (selectedBooks.length === 0) {
        alert("Vui lòng chọn ít nhất một cuốn sách để mượn!");
        return;
    }

    if (!confirm("Xác nhận tạo phiếu mượn cho độc giả này?")) return;

    try {
        const response = await fetch('/staff/api/create-borrow-slip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                book_ids: selectedBooks
            })
        });

        const result = await response.json();

        if (result.success) {
            alert("Cho mượn thành công!");
            // Chuyển hướng về trang quản lý mượn trả
            window.location.href = "/staff/orders";
        } else {
            alert("Lỗi: " + result.message);
        }
    } catch (error) {
        console.error("Lỗi gửi dữ liệu:", error);
        alert("Có lỗi xảy ra khi tạo phiếu mượn!");
    }
}