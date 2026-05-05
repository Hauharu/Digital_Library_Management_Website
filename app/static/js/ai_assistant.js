document.addEventListener('DOMContentLoaded', function() {
    const fab = document.getElementById('aiAssistantFab');
    const chatWindow = document.getElementById('aiChatWindow');
    const closeBtn = document.getElementById('aiChatClose');
    const sendBtn = document.getElementById('aiChatSend');
    const inputField = document.getElementById('aiChatInput');
    const messagesContainer = document.getElementById('aiChatMessages');

    if (!fab || !chatWindow) {
        console.error('AI Assistant: Các thành phần giao diện không tìm thấy.');
        return;
    }

    // 1. Tải lịch sử chat từ sessionStorage khi trang web load
    try {
        const savedHistory = sessionStorage.getItem('ai_chat_history');
        if (savedHistory) {
            messagesContainer.innerHTML = ''; 
            const history = JSON.parse(savedHistory);
            history.forEach(msg => {
                appendMessage(msg.sender, msg.text, false);
            });
        }
    } catch (e) {
        console.error('Lỗi tải lịch sử chat:', e);
    }

    function toggleChat() {
        chatWindow.classList.toggle('active');
        console.log('Toggle chat window');
    }

    // 2. Hàm thêm tin nhắn
    function appendMessage(sender, text, save = true) {
        if (!messagesContainer) return;
        
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        
        if (sender === 'bot') {
            // Kiểm tra thư viện marked có tồn tại không
            if (typeof marked !== 'undefined') {
                msgDiv.innerHTML = marked.parse(text);
            } else {
                msgDiv.innerText = text;
            }
        } else {
            msgDiv.textContent = text;
        }
        
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        if (save) {
            const history = JSON.parse(sessionStorage.getItem('ai_chat_history') || '[]');
            history.push({ sender, text });
            sessionStorage.setItem('ai_chat_history', JSON.stringify(history));
        }
    }

    // 3. Hàm gửi tin nhắn
    function sendMessage() {
        const message = inputField.value.trim();
        if (!message) return;

        appendMessage('user', message);
        inputField.value = '';

        const typingId = 'typing-' + Date.now();
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.id = typingId;
        typingDiv.textContent = '...';
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        fetch('/ai/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            const el = document.getElementById(typingId);
            if (el) el.remove();
            appendMessage('bot', data.reply);
        })
        .catch(err => {
            const el = document.getElementById(typingId);
            if (el) el.remove();
            appendMessage('bot', 'Xin lỗi, hệ thống đang bận. Bạn vui lòng thử lại sau!');
        });
    }

    // Gán sự kiện
    fab.addEventListener('click', function(e) {
        e.preventDefault();
        toggleChat();
    });

    if (closeBtn) closeBtn.addEventListener('click', toggleChat);
    if (sendBtn) sendBtn.addEventListener('click', sendMessage);
    if (inputField) {
        inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }
});
