/* 1. ĐỊNH NGHĨA HÀM TRƯỚC (Để HTML gọi được ngay) */
function togglePassword(inputId) {
    const passwordInput = document.getElementById(inputId);
    const eyeIcon = document.getElementById('eye-icon-' + inputId);

    if (!passwordInput || !eyeIcon) {
        console.warn(`Không tìm thấy: ${inputId} hoặc eye-icon-${inputId}`);
        return;
    }

    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        eyeIcon.classList.replace('fa-eye', 'fa-eye-slash');
    } else {
        passwordInput.type = "password";
        eyeIcon.classList.replace('fa-eye-slash', 'fa-eye');
    }
}

/* 2. CÁC LOGIC CHẠY SAU KHI LOAD TRANG */
document.addEventListener('DOMContentLoaded', function() {
    console.log("OU BOOK: Register JS Ready!");

    // --- Xử lý Alert ---
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                alert.style.opacity = "0";
                setTimeout(() => alert.remove(), 500);
            }
        }, 5000);
    });

    // --- Kiểm tra mật khẩu khớp nhau khi Submit ---
    const registerForm = document.querySelector('.needs-validation');
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');

    if (registerForm && password && confirmPassword) {
        registerForm.addEventListener('submit', function(event) {
            // Kiểm tra khớp mật khẩu
            if (password.value !== confirmPassword.value) {
                event.preventDefault();
                event.stopPropagation();

                confirmPassword.setCustomValidity("Mật khẩu không khớp");
                confirmPassword.classList.add('is-invalid');
            } else {
                confirmPassword.setCustomValidity("");
                confirmPassword.classList.remove('is-invalid');
            }

            registerForm.classList.add('was-validated');
        }, false);

        // Xóa thông báo lỗi khi người dùng đang gõ lại
        confirmPassword.addEventListener('input', function() {
            if (password.value === password.value) {
                confirmPassword.setCustomValidity("");
                confirmPassword.classList.remove('is-invalid');
            }
        });
    }
});