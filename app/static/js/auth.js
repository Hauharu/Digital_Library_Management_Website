/**
 * Auth Common Logic
 */

// Hàm ẩn/hiện mật khẩu
function togglePassword(inputId) {
    const passwordInput = document.getElementById(inputId);
    const eyeIcon = document.getElementById('eye-icon-' + inputId);

    if (!passwordInput || !eyeIcon) return;

    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        eyeIcon.classList.replace('fa-eye', 'fa-eye-slash');
    } else {
        passwordInput.type = "password";
        eyeIcon.classList.replace('fa-eye-slash', 'fa-eye');
    }
}
