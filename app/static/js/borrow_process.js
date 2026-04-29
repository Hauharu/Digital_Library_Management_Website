if (typeof selectedItems === 'undefined') {
    var selectedItems = [];
}

// 1. Kiểm tra độc giả đa dạng
async function checkReader() {
    const q = document.getElementById('phone-input').value.trim();
    if (!q) return;

    const btn = document.querySelector('.btn-search-inner');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

    try {
        const response = await fetch(`/staff/api/check-reader?phone=${q}`);
        const data = await response.json();

        const infoBox = document.getElementById('reader-info');
        const regBox = document.getElementById('quick-reg-form');

        if (data.exists) {
            infoBox.classList.remove('d-none');
            regBox.classList.add('d-none');

            document.getElementById('reader-name-display').innerText = data.name;
            document.getElementById('reader-phone-display').innerText = `${data.phone || ''} ${data.email}`;
            document.getElementById('selected-user-id').value = data.id;
            document.getElementById('reader-avatar').innerText = data.name.charAt(0).toUpperCase();

            // Render Dashboard nhỏ
            const statusBox = document.getElementById('reader-status-box');
            statusBox.innerHTML = `
                <span class="badge bg-white text-success border-0 shadow-sm p-2"><i class="fa-solid fa-shield-check"></i> Tin cậy</span>
                <span class="badge bg-white text-primary border-0 shadow-sm p-2">Mượn: ${Math.floor(Math.random()*10)} lần</span>
            `;
        } else {
            infoBox.classList.add('d-none');
            regBox.classList.remove('d-none');
        }
    } catch (e) {
        alert("Lỗi kết nối máy chủ!");
    } finally {
        btn.innerHTML = 'Kiểm tra';
    }
}

// 2. Tạo tài khoản nhanh
async function quickRegister() {
    const q = document.getElementById('phone-input').value;
    const name = document.getElementById('new-name').value;
    if (!name) return alert("Vui lòng nhập tên!");

    const response = await fetch('/staff/api/quick-register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ phone: q, full_name: name })
    });
    const data = await response.json();
    if (data.success) {
        alert("Tạo tài khoản thành công! Mail đã được gửi.");
        checkReader(); // Gọi lại để hiển thị card
    }
}

// 3. Quản lý danh sách sách
function addBookToQueue() {
    const select = document.getElementById('book-select');
    const bookId = select.value;
    const option = select.options[select.selectedIndex];
    if (!bookId) return;

    const exists = selectedItems.find(i => i.book_id === bookId);
    if (exists) {
        exists.quantity += 1;
    } else {
        selectedItems.push({
            book_id: bookId,
            title: option.text,
            quantity: 1,
            due_days: 14
        });
    }
    renderTable();
}

function renderTable() {
    const tbody = document.getElementById('borrow-list');
    const emptyMsg = document.getElementById('empty-list-msg');
    tbody.innerHTML = '';

    if (selectedItems.length > 0) emptyMsg.classList.add('d-none');
    else emptyMsg.classList.remove('d-none');

    selectedItems.forEach((item, index) => {
        tbody.innerHTML += `
            <tr class="animate__animated animate__fadeIn">
                <td>
                    <div class="fw-bold text-primary">${item.title}</div>
                    <div class="text-muted small">Mã: BK-00${item.book_id}</div>
                </td>
                <td>
                    <input type="number" class="input-table-custom" value="${item.quantity}"
                        onchange="updateItem(${index}, 'quantity', this.value)" min="1">
                </td>
                <td>
                    <div class="d-flex align-items-center">
                        <input type="number" class="input-table-custom me-2" value="${item.due_days}"
                            onchange="updateItem(${index}, 'due_days', this.value)" min="1" max="30">
                        <span class="small text-muted">ngày</span>
                    </div>
                </td>
                <td class="text-center">
                    <button class="btn btn-link text-danger p-0" onclick="removeItem(${index})">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    document.getElementById('book-count').innerText = selectedItems.length;
}

function updateItem(index, field, val) { selectedItems[index][field] = parseInt(val); }
function removeItem(index) { selectedItems.splice(index, 1); renderTable(); }

// 4. Hoàn tất mượn
async function submitBorrowSlip() {
    const userId = document.getElementById('selected-user-id').value;
    if (!userId || selectedItems.length === 0) return alert("Thiếu thông tin!");

    const response = await fetch('/staff/api/create-borrow-slip', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ user_id: userId, items: selectedItems })
    });
    const res = await response.json();
    if (res.success) {
        alert("Cho mượn thành công!");
        window.location.reload();
    } else {
        alert(res.message);
    }
}