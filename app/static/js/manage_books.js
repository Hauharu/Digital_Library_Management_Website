// Đợi DOM load xong mới thực thi
document.addEventListener('DOMContentLoaded', function() {

    // 1. Xử lý nút "Thêm sách mới"
    const addBtn = document.querySelector('[data-bs-target="#addBookModal"]');
    if (addBtn) {
        addBtn.addEventListener('click', (e) => {
            // Ngăn chặn hành vi mặc định nếu cần
            const form = document.getElementById('bookForm');
            form.reset();
            // Đảm bảo action đúng với route thêm sách trong Python
            form.action = '/staff/add-book';
            document.getElementById('modalTitle').innerText = 'Thêm ấn phẩm mới';
            document.getElementById('btnSubmit').innerText = 'Lưu dữ liệu';

            // Nếu bạn dùng chung modal 'bookModal' cho cả thêm và sửa:
            const myModal = new bootstrap.Modal(document.getElementById('bookModal'));
            myModal.show();
        });
    }
});

// 2. Hàm mở Modal chỉnh sửa (Sửa lại selector để lấy đủ các trường mới)
async function openEditModal(bookId) {
    console.log("Đang lấy dữ liệu cho sách ID:", bookId);
    try {
        // Lưu ý: nên dùng đường dẫn tuyệt đối /staff/api/... để tránh lỗi route
        const response = await fetch(`/staff/api/book/${bookId}`);
        if (!response.ok) throw new Error("Không thể kết nối với máy chủ");

        const book = await response.json();
        const form = document.getElementById('bookForm');

        // Đổi action sang route edit
        form.action = `/staff/edit-book/${book.id}`;
        document.getElementById('modalTitle').innerText = 'Chỉnh sửa: ' + book.title;
        document.getElementById('btnSubmit').innerText = 'Cập nhật thay đổi';

        // Điền dữ liệu vào các ô input (Dùng querySelector để chính xác)
        form.querySelector('[name="title"]').value = book.title || '';
        form.querySelector('[name="author"]').value = book.author || '';
        form.querySelector('[name="isbn"]').value = book.isbn || '';
        form.querySelector('[name="price"]').value = book.price || 0;
        form.querySelector('[name="total_quantity"]').value = book.total_quantity || 0;
        form.querySelector('[name="category_id"]').value = book.category_id;
        form.querySelector('[name="description"]').value = book.description || '';

        // --- THÊM CÁC TRƯỜNG MỚI THEO MODEL ---
        if(form.querySelector('[name="language"]'))
            form.querySelector('[name="language"]').value = book.language || '';
        if(form.querySelector('[name="publication_info"]'))
            form.querySelector('[name="publication_info"]').value = book.publication_info || '';

        const myModal = new bootstrap.Modal(document.getElementById('bookModal'));
        myModal.show();
    } catch (e) {
        console.error(e);
        alert("Lỗi: " + e.message);
    }
}

// 3. Hàm xem chi tiết (Thêm hiển thị Ngôn ngữ & NXB)
async function openViewModal(bookId) {
    try {
        const response = await fetch(`/staff/api/book/${bookId}`);
        if (!response.ok) throw new Error("Lỗi tải thông tin");
        const book = await response.json();

        // Gán dữ liệu vào Modal View
        document.getElementById('view-book-title').innerText = book.title;
        document.getElementById('view-book-author').innerText = book.author;
        document.getElementById('view-book-category').innerText = book.category_name;
        document.getElementById('view-book-isbn').innerText = book.isbn || '---';

        // Hiển thị thêm các trường mới
        if(document.getElementById('view-book-language'))
            document.getElementById('view-book-language').innerText = book.language || 'Tiếng Việt';
        if(document.getElementById('view-book-pub'))
            document.getElementById('view-book-pub').innerText = book.publication_info || 'Chưa rõ NXB';

        // Format tiền tệ Việt Nam
        document.getElementById('view-book-price').innerText = new Intl.NumberFormat('vi-VN').format(book.price) + ' đ';

        document.getElementById('view-book-stock').innerText = `${book.available_quantity} / ${book.total_quantity}`;
        document.getElementById('view-book-description').innerText = book.description || 'Không có mô tả.';

        const imgTag = document.getElementById('view-book-image');
        // Nếu có ảnh thì dùng, không thì dùng ảnh mặc định của bạn
        imgTag.src = book.image ? book.image : '/static/images/sachmau.png';

        const viewModal = new bootstrap.Modal(document.getElementById('viewBookModal'));
        viewModal.show();
    } catch (e) {
        console.error(e);
        alert("Lỗi: " + e.message);
    }
}

// 4. Xác nhận xóa
function confirmDelete(bookId) {
    const form = document.getElementById('deleteForm');
    form.action = `/staff/delete-book/${bookId}`;
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
    deleteModal.show();
}