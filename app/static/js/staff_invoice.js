function showInvoiceDetail(invoiceId) {
    fetch(`/staff/api/invoice/${invoiceId}`)
        .then(response => response.json())
        .then(data => {
            // Thông tin chung
            document.getElementById('m_inv_id').innerText = '#' + data.id;
            document.getElementById('m_amount').innerText = data.amount.toLocaleString() + 'đ';
            document.getElementById('m_total_final').innerText = data.amount.toLocaleString() + 'đ';
            document.getElementById('m_date').innerText = data.date;

            // Thông tin độc giả
            document.getElementById('m_user').innerText = data.user_name;
            document.getElementById('m_phone').innerText = data.user_phone;
            document.getElementById('m_email').innerText = data.user_email;

            // Thông tin phiếu mượn
            document.getElementById('m_book').innerText = data.book_title;
            document.getElementById('m_slip_id').innerText = data.slip_id;
            document.getElementById('m_due_date').innerText = data.due_date;

            // Lý do phạt (Lấy từ incident report nếu có)
            document.getElementById('m_description').innerText = data.incident_desc || "Vi phạm thời gian trả sách hoặc hư hỏng thiết bị.";

            new bootstrap.Modal(document.getElementById('invoiceDetailModal')).show();
        });
}
function openConfirmModal(actionUrl) {
    document.getElementById('confirmPaymentForm').action = actionUrl;
    new bootstrap.Modal(document.getElementById('confirmPaymentModal')).show();
}