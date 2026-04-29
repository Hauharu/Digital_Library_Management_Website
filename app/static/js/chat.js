document.addEventListener('DOMContentLoaded', () => {
    // Sử dụng socket toàn cầu từ base.html
    const chatBox = document.getElementById('chat-box');
    const msgInput = document.getElementById('msg-input');
    const sendBtn = document.getElementById('btn-send-msg');
    const bookId = document.getElementById('book-id-data').dataset.bookId;
    const currentUserId = parseInt(document.getElementById('user-id-data')?.dataset.userId || 0);

    // Join room
    socket.emit('join', { book_id: bookId });

    // Cuộn xuống cuối chat
    const scrollToBottom = () => {
        chatBox.scrollTop = chatBox.scrollHeight;
    };
    scrollToBottom();

    // Gửi tin nhắn
    const sendMessage = () => {
        const text = msgInput.value.trim();
        const rating = document.getElementById('selected-rating').value; // Lấy số sao
        
        if (text || rating) { // Chỉ gửi nếu có chữ HOẶC có sao
            socket.emit('send_message', {
                book_id: bookId,
                message: text,
                rating: rating ? parseInt(rating) : null
            });
            msgInput.value = '';
            // Reset stars after sending
            document.getElementById('selected-rating').value = '';
            document.querySelectorAll('.star-rating-chat i').forEach(s => s.classList.replace('fa-solid', 'fa-regular'));
        }
    };

    sendBtn?.addEventListener('click', sendMessage);
    msgInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Hàm xóa tin nhắn
    window.deleteMessage = (msgId) => {
        if (confirm('Bạn có chắc chắn muốn xóa bình luận này?')) {
            socket.emit('delete_message', { msg_id: msgId });
        }
    };

    // Hàm thích bình luận
    window.likeReview = (revId) => {
        if (!currentUserId) {
            alert('Vui lòng đăng nhập để thực hiện tính năng này');
            return;
        }
        socket.emit('like_review', { rev_id: revId });
    };

    // Hàm hiện khung phản hồi
    window.toggleReplyInput = (revId) => {
        if (!currentUserId) {
            alert('Vui lòng đăng nhập để thực hiện tính năng này');
            return;
        }
        const replyArea = document.getElementById(`reply-area-${revId}`);
        if (replyArea) {
            replyArea.classList.toggle('d-none');
            const input = replyArea.querySelector('input');
            if (!replyArea.classList.contains('d-none')) {
                input.focus();
            }
        }
    };

    // Hàm gửi phản hồi
    window.sendReply = (revId) => {
        const input = document.querySelector(`#reply-area-${revId} input`);
        const content = input.value.trim();
        if (content) {
            socket.emit('reply_review', { rev_id: revId, content: content });
            input.value = '';
            document.getElementById(`reply-area-${revId}`).classList.add('d-none');
        }
    };

    // Khi tin nhắn bị xóa
    socket.on('message_deleted', (data) => {
        const msgElement = document.getElementById(`msg-actions-${data.msg_id}`)?.closest('.chat-message');
        if (msgElement) {
            msgElement.style.opacity = '0';
            setTimeout(() => msgElement.remove(), 300);
            
            // Cập nhật số lượng trên icon
            const countEl = document.getElementById('top-comment-count');
            const countInnerEl = document.getElementById('top-comment-count-inner');
            if (countEl) {
                const currentCount = parseInt(countEl.innerText) || 0;
                const newCount = Math.max(0, currentCount - 1);
                countEl.innerText = `${newCount} Bình luận`;
                if (countInnerEl) countInnerEl.innerText = newCount;

                // Hiện lại placeholder nếu hết bình luận
                if (newCount === 0) {
                    document.getElementById('no-comments-placeholder')?.classList.remove('d-none');
                }
            }
            
            // Hiện lại khung nhập liệu (vì mỗi người chỉ có 1 bài, xóa đi thì được viết lại)
            document.querySelector('.chat-input-area')?.classList.remove('d-none');

            // Cập nhật Sao trên icon đầu trang với điểm trung bình mới
            if (typeof data.new_avg !== 'undefined') {
                const starsDisplay = document.getElementById('top-stars-display');
                const ratingText = document.getElementById('top-rating-text');
                if (starsDisplay) {
                    const rVal = Math.floor(data.new_avg);
                    let starsHtml = '';
                    for (let i = 0; i < rVal; i++) starsHtml += '<i class="fa-solid fa-star" style="color: #f39c12 !important;"></i>';
                    for (let i = 0; i < (5 - rVal); i++) starsHtml += '<i class="fa-regular fa-star" style="color: #f39c12 !important;"></i>';
                    starsDisplay.innerHTML = starsHtml;
                }
                if (ratingText) {
                    ratingText.innerText = `${data.new_avg.toFixed(1)}/5`;
                }
            }
        }
    });

    // Khi có ai đó thích bình luận
    socket.on('review_liked', (data) => {
        const likeBtn = document.getElementById(`like-btn-${data.rev_id}`);
        const likeCount = document.getElementById(`like-count-${data.rev_id}`);
        if (likeCount) {
            likeCount.innerText = data.like_count > 0 ? data.like_count : '';
        }
        if (likeBtn && data.user_id === currentUserId) {
            if (data.liked) {
                likeBtn.classList.add('text-primary');
                likeBtn.classList.remove('text-muted');
                likeBtn.querySelector('i').classList.replace('fa-regular', 'fa-solid');
            } else {
                likeBtn.classList.remove('text-primary');
                likeBtn.classList.add('text-muted');
                likeBtn.querySelector('i').classList.replace('fa-solid', 'fa-regular');
            }
        }
    });

    // Khi có phản hồi mới
    socket.on('receive_reply', (data) => {
        const replyList = document.getElementById(`reply-list-${data.rev_id}`);
        if (replyList) {
            const replyHtml = `
                <div class="reply-item d-flex gap-2 mt-2 p-2 rounded bg-light" style="font-size: 13px;">
                    <img src="${data.avatar || 'https://res.cloudinary.com/dwwfgtxv4/image/upload/v1776585521/AnhDaiDien_nvnfre.png'}" 
                         style="width: 24px; height: 24px; border-radius: 50%; object-fit: cover;">
                    <div>
                        <div class="d-flex align-items-center gap-2">
                            <span class="fw-bold">${data.user}</span>
                            <span class="text-muted" style="font-size: 11px;">${data.time}</span>
                        </div>
                        <div class="reply-content">${data.content}</div>
                    </div>
                </div>
            `;
            replyList.insertAdjacentHTML('beforeend', replyHtml);
        }
    });

    // Nhận tin nhắn
    socket.on('receive_message', (data) => {
        // Ẩn placeholder khi có tin nhắn
        document.getElementById('no-comments-placeholder')?.classList.add('d-none');

        const isOwn = data.user_id === currentUserId;
        
        // Nếu là tin nhắn của chính mình, ẩn khung nhập liệu đi
        if (isOwn) {
            document.querySelector('.chat-input-area')?.classList.add('d-none');
        }

        const msgHtml = `
            <div class="chat-message border-bottom pb-4 mb-4 bg-white p-3 rounded-3 shadow-sm" id="msg-container-${data.msg_id}">
                <img src="${data.avatar || 'https://res.cloudinary.com/dwwfgtxv4/image/upload/v1776585521/AnhDaiDien_nvnfre.png'}" class="chat-avatar">
                <div class="message-wrapper">
                    <div class="message-info">
                        <span class="sender-name">${data.user}</span>
                        <span class="message-time small">• ${data.time}</span>
                    </div>
                    ${data.rating ? `
                        <div class="message-rating mb-2" style="font-size: 14px;">
                            ${Array(data.rating).fill('<i class="fa-solid fa-star" style="color: #f39c12 !important;"></i>').join('')}
                            ${Array(5 - data.rating).fill('<i class="fa-regular fa-star" style="color: #f39c12 !important;"></i>').join('')}
                        </div>` : ''}
                    <div class="message-bubble mb-3">
                        ${data.message || '<i class="text-muted small">Người dùng chỉ chấm điểm sao</i>'}
                    </div>
                    <div class="message-actions" id="msg-actions-${data.msg_id}">
                        <span class="action-link text-muted small" id="like-btn-${data.msg_id}" onclick="likeReview(${data.msg_id})">
                            <i class="fa-regular fa-thumbs-up"></i> Thích <span id="like-count-${data.msg_id}"></span>
                        </span>
                        <span class="action-link text-primary small ms-3" onclick="toggleReplyInput(${data.msg_id})">
                            <i class="fa-regular fa-comment-dots"></i> Phản hồi
                        </span>
                        ${isOwn ? 
                            `<span class="action-link text-danger small ms-3" onclick="deleteMessage(${data.msg_id})"><i class="fa-regular fa-trash-can"></i> Xóa</span>` : 
                            ''
                        }
                    </div>
                    <div id="reply-list-${data.msg_id}" class="reply-list ms-4 mt-2"></div>
                    <div id="reply-area-${data.msg_id}" class="reply-input-area ms-4 mt-2 d-none">
                        <div class="input-group input-group-sm">
                            <input type="text" class="form-control" placeholder="Viết phản hồi...">
                            <button class="btn btn-primary" type="button" onclick="sendReply(${data.msg_id})">Gửi</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // KIỂM TRA: Nếu tin nhắn ID này đã tồn tại trên màn hình (trường hợp cập nhật), thì thay thế nó
        const existingMsg = document.getElementById(`msg-container-${data.msg_id}`);
        if (existingMsg) {
            existingMsg.outerHTML = msgHtml;
        } else {
            chatBox.insertAdjacentHTML('beforeend', msgHtml);
            // Chỉ tăng số lượng bình luận nếu là tin nhắn mới hoàn toàn
            const countEl = document.getElementById('top-comment-count');
            const countInnerEl = document.getElementById('top-comment-count-inner');
            if (countEl) {
                const currentCount = parseInt(countEl.innerText) || 0;
                const newCount = currentCount + 1;
                countEl.innerText = `${newCount} Bình luận`;
                if (countInnerEl) countInnerEl.innerText = newCount;
            }
        }

        // Cập nhật Sao trên icon đầu trang (Tạm thời cập nhật theo đánh giá mới nhất)
        if (data.rating) {
            const starsDisplay = document.getElementById('top-stars-display');
            const ratingText = document.getElementById('top-rating-text');
            if (starsDisplay) {
                let starsHtml = '';
                for(let i=0; i<data.rating; i++) starsHtml += '<i class="fa-solid fa-star" style="color: #f39c12 !important;"></i>';
                for(let i=0; i<(5-data.rating); i++) starsHtml += '<i class="fa-regular fa-star" style="color: #f39c12 !important;"></i>';
                starsDisplay.innerHTML = starsHtml;
            }
            if (ratingText) {
                ratingText.innerText = `${data.rating.toFixed(1)}/5`;
            }
        }
        
        scrollToBottom();
    });
});
