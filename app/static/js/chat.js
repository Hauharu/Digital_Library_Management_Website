document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
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
        if (text) {
            socket.emit('send_message', {
                book_id: bookId,
                message: text
            });
            msgInput.value = '';
        }
    };

    sendBtn?.addEventListener('click', sendMessage);
    msgInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Nhận tin nhắn
    socket.on('receive_message', (data) => {
        const isOwn = data.user_id === currentUserId;
        const msgHtml = `
            <div class="chat-message ${isOwn ? 'own' : ''}">
                <img src="${data.avatar || '/static/img/default-avatar.png'}" class="chat-avatar">
                <div class="message-wrapper">
                    <div class="message-info">
                        <span class="sender-name">${data.user}</span>
                        <span class="message-time">${data.time}</span>
                    </div>
                    <div class="message-bubble">
                        ${data.message}
                    </div>
                </div>
            </div>
        `;
        chatBox.insertAdjacentHTML('beforeend', msgHtml);
        scrollToBottom();
    });
});
