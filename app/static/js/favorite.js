function toggleFavorite(bookId) {
    fetch(`/toggle-favorite/${bookId}`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.status === 401) {
            alert('Vui lòng đăng nhập để thực hiện chức năng này');
            window.location.href = '/login';
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data) {
            const icon = document.getElementById('favorite-icon');
            const text = document.getElementById('favorite-text');
            
            if (data.status === 'added') {
                if (icon) {
                    icon.classList.remove('fa-regular');
                    icon.classList.add('fa-solid', 'text-danger');
                }
                if (text) text.innerText = 'Đã thích';
            } else if (data.status === 'removed') {
                if (icon) {
                    icon.classList.remove('fa-solid', 'text-danger');
                    icon.classList.add('fa-regular');
                }
                if (text) text.innerText = 'Yêu thích';
            }
        }
    })
    .catch(error => console.error('Error:', error));
}

function toggleFavoriteCard(el, bookId) {
    fetch(`/toggle-favorite/${bookId}`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.status === 401) {
            alert('Vui lòng đăng nhập để thực hiện chức năng này');
            window.location.href = '/login';
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data) {
            const icon = el.querySelector('i');
            if (data.status === 'added') {
                icon.classList.remove('fa-regular');
                icon.classList.add('fa-solid', 'text-danger');
            } else if (data.status === 'removed') {
                icon.classList.remove('fa-solid', 'text-danger');
                icon.classList.add('fa-regular');
            }
        }
    })
    .catch(error => console.error('Error:', error));
}
