function handleReturn(id, title) {
    document.getElementById('returnBookTitle').innerText = title;
    document.getElementById('returnForm').action = "/staff/confirm-return/" + id;
    new bootstrap.Modal(document.getElementById('returnModal')).show();
}

function handleReport(id, title) {
    document.getElementById('reportBookTitle').innerText = title;
    document.getElementById('reportForm').action = "/staff/report-issue/" + id;
    new bootstrap.Modal(document.getElementById('reportModal')).show();
}

function handleDetail(id) {
    new bootstrap.Modal(document.getElementById('modal-' + id)).show();
}