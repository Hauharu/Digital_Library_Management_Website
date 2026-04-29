
function openAddUserModal() {
    const form = document.getElementById('userForm');
    form.reset();
    form.action = '/admin/users/add';
    document.getElementById('userModalTitle').innerText = 'Tạo tài khoản mới';
    document.getElementById('userBtnSubmit').innerText = 'Tạo ngay';
    new bootstrap.Modal(document.getElementById('userModal')).show();
}

async function openEditUserModal(userId) {
    try {
        const res = await fetch(`/admin/api/user/${userId}`);
        const user = await res.json();

        const form = document.getElementById('userForm');
        form.action = `/admin/users/edit/${userId}`;
        document.getElementById('userModalTitle').innerText = 'Chỉnh sửa tài khoản';
        document.getElementById('userBtnSubmit').innerText = 'Cập nhật';

        form.querySelector('[name="last_name"]').value = user.last_name;
        form.querySelector('[name="first_name"]').value = user.first_name;
        form.querySelector('[name="username"]').value = user.username;
        form.querySelector('[name="email"]').value = user.email;
        form.querySelector('[name="phone_number"]').value = user.phone_number || '';
        form.querySelector('[name="gender"]').value = user.gender;
        form.querySelector('[name="role"]').value = user.role;

        new bootstrap.Modal(document.getElementById('userModal')).show();
    } catch (e) { alert("Lỗi khi lấy dữ liệu!"); }
}

async function openViewUserModal(userId) {
    try {
        const res = await fetch(`/admin/api/user/${userId}`);
        const user = await res.json();

        document.getElementById('v-avatar').src = user.avatar;
        document.getElementById('v-full-name').innerText = `${user.last_name} ${user.first_name}`;
        document.getElementById('v-role').innerText = user.role;
        document.getElementById('v-username').innerText = user.username;
        document.getElementById('v-email').innerText = user.email;
        document.getElementById('v-phone').innerText = user.phone_number || 'Chưa cập nhật';

        new bootstrap.Modal(document.getElementById('viewUserModal')).show();
    } catch (e) { alert("Lỗi hiển thị chi tiết!"); }
}

function confirmDeleteUser(userId) {

    const deleteForm = document.getElementById('deleteUserForm');

    if (!deleteForm) {
        console.error("Không tìm thấy form có ID 'deleteUserForm'");
        return;
    }

    deleteForm.action = `/admin/users/delete/${userId}`;

    const modalElement = document.getElementById('deleteUserModal');
    if (modalElement) {
        const deleteModal = new bootstrap.Modal(modalElement);
        deleteModal.show();
    } else {
        console.error("Không tìm thấy Modal có ID 'deleteUserModal'");
    }
}
document.addEventListener("DOMContentLoaded", function() {

    const urlParams = new URLSearchParams(window.location.search);

    if (urlParams.has('page')) {
        const readerTabBtn = document.querySelector('[data-bs-target="#reader-panel"]');
        if (readerTabBtn) {
            const tab = new bootstrap.Tab(readerTabBtn);
            tab.show();
        }
    }
});