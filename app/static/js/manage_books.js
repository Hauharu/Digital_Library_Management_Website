document.querySelector('[data-bs-target="#addBookModal"]')?.addEventListener('click', () => {
    const form = document.getElementById('bookForm');
    form.reset();
    form.action = '/staff/add-book';
    document.getElementById('modalTitle').innerText = 'Thêm sách mới';
    document.getElementById('btnSubmit').innerText = 'Lưu dữ liệu';
    new bootstrap.Modal(document.getElementById('bookModal')).show();
});

async function openEditModal(bookId) {
    console.log("Đang lấy dữ liệu cho sách ID:", bookId);
    try {
        const response = await fetch(`/staff/api/book/${bookId}`);
        if (!response.ok) throw new Error("Mạng có vấn đề");

        const book = await response.json();
        console.log("Dữ liệu nhận được:", book);

        const form = document.getElementById('bookForm');
        // Quan trọng: Đổi action của form sang route edit
        form.action = `/staff/edit-book/${book.id}`;

        document.getElementById('modalTitle').innerText = 'Chỉnh sửa thông tin: ' + book.title;
        document.getElementById('btnSubmit').innerText = 'Cập nhật thay đổi';

        // Điền dữ liệu vào các ô input
        form.querySelector('[name="title"]').value = book.title;
        form.querySelector('[name="author"]').value = book.author;
        form.querySelector('[name="isbn"]').value = book.isbn;
        form.querySelector('[name="price"]').value = book.price;
        form.querySelector('[name="total_quantity"]').value = book.total_quantity;
        form.querySelector('[name="category_id"]').value = book.category_id;
        form.querySelector('[name="description"]').value = book.description;

        // Kích hoạt Modal của Bootstrap
        const myModal = new bootstrap.Modal(document.getElementById('bookModal'));
        myModal.show();
    } catch (e) {
        console.error(e);
        alert("Lỗi: Không thể tải dữ liệu sách. Hãy kiểm tra console!");
    }
}
async function openViewModal(bookId) {
    try {
        const response = await fetch(`./api/book/${bookId}`);
        if (!response.ok) throw new Error("Lỗi mạng");
        const book = await response.json();

        document.getElementById('view-book-title').innerText = book.title;
        document.getElementById('view-book-author').innerText = `Tác giả: ${book.author}`;
        document.getElementById('view-book-category').innerText = book.category_name; // Nhớ check API trả về tên hay ID
        document.getElementById('view-book-isbn').innerText = book.isbn || 'N/A';
        document.getElementById('view-book-price').innerText = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(book.price);
        document.getElementById('view-book-stock').innerText = `Còn ${book.available_quantity} / Tổng ${book.total_quantity}`;
        document.getElementById('view-book-description').innerText = book.description || 'Không có mô tả chi tiết.';
        
        const imgTag = document.getElementById('view-book-image');
        imgTag.src = book.image ? book.image : 'https://via.placeholder.com/300x450?text=No+Cover';

        new bootstrap.Modal(document.getElementById('viewBookModal')).show();
    } catch (e) {
        console.error(e);
        alert("Không thể tải thông tin chi tiết!");
    }
}
function confirmDelete(bookId) {
    const form = document.getElementById('deleteForm');
    form.action = `/staff/delete-book/${bookId}`;
    new bootstrap.Modal(document.getElementById('deleteConfirmModal')).show();
}